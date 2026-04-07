package engine

import (
	"errors"
	"sync"
	"time"
)

var errFlushFailed = errors.New("flush failed")

// MetricEvent is a typed metric emitted through the pipeline.
type MetricEvent struct {
	Kind   string            // "counter", "gauge", "timer"
	Name   string
	Value  float64
	Labels map[string]string
	Time   time.Time
}

// Flusher sends a batch of metrics to an external sink (e.g. Supabase).
type Flusher func([]MetricEvent) error

// PipelineOption configures the MetricsPipeline.
type PipelineOption func(*MetricsPipeline)

// WithFlushInterval sets how often the pipeline flushes.
func WithFlushInterval(d time.Duration) PipelineOption {
	return func(mp *MetricsPipeline) {
		mp.flushInterval = d
	}
}

// WithMaxRetries sets the number of flush retries on error.
func WithMaxRetries(n int) PipelineOption {
	return func(mp *MetricsPipeline) {
		mp.maxRetries = n
	}
}

// MetricsPipeline collects metrics via channels and flushes in batches.
type MetricsPipeline struct {
	ch            chan MetricEvent
	flusher       Flusher
	flushInterval time.Duration
	maxRetries    int
	done          chan struct{}
	wg            sync.WaitGroup
}

// NewMetricsPipeline creates a pipeline and starts the collector goroutine.
func NewMetricsPipeline(f Flusher, opts ...PipelineOption) *MetricsPipeline {
	mp := &MetricsPipeline{
		ch:            make(chan MetricEvent, 1024),
		flusher:       f,
		flushInterval: 30 * time.Second,
		maxRetries:    3,
		done:          make(chan struct{}),
	}
	for _, opt := range opts {
		opt(mp)
	}
	mp.wg.Add(1)
	go mp.collect()
	return mp
}

func (mp *MetricsPipeline) collect() {
	defer mp.wg.Done()
	ticker := time.NewTicker(mp.flushInterval)
	defer ticker.Stop()

	var buf []MetricEvent

	for {
		select {
		case <-mp.done:
			// Drain remaining events before exit
			for {
				select {
				case ev := <-mp.ch:
					buf = append(buf, ev)
				default:
					if len(buf) > 0 {
						mp.flushWithRetry(buf)
					}
					return
				}
			}
		case ev := <-mp.ch:
			buf = append(buf, ev)
		case <-ticker.C:
			if len(buf) > 0 {
				mp.flushWithRetry(buf)
				buf = nil
			}
		}
	}
}

func (mp *MetricsPipeline) flushWithRetry(batch []MetricEvent) {
	snapshot := make([]MetricEvent, len(batch))
	copy(snapshot, batch)

	for attempt := 0; attempt <= mp.maxRetries; attempt++ {
		if err := mp.flusher(snapshot); err == nil {
			return
		}
		if attempt < mp.maxRetries {
			time.Sleep(time.Duration(1<<uint(attempt)) * 10 * time.Millisecond)
		}
	}
}

// Stop shuts down the collector goroutine and flushes remaining events.
func (mp *MetricsPipeline) Stop() {
	select {
	case <-mp.done:
		return
	default:
		close(mp.done)
	}
	mp.wg.Wait()
}

func (mp *MetricsPipeline) emit(kind, name string, value float64, labels map[string]string) {
	select {
	case mp.ch <- MetricEvent{
		Kind:   kind,
		Name:   name,
		Value:  value,
		Labels: labels,
		Time:   time.Now(),
	}:
	case <-mp.done:
	}
}

// Counter emits a counter metric.
func (mp *MetricsPipeline) Counter(name string, value float64, labels map[string]string) {
	mp.emit("counter", name, value, labels)
}

// Gauge emits a gauge metric.
func (mp *MetricsPipeline) Gauge(name string, value float64, labels map[string]string) {
	mp.emit("gauge", name, value, labels)
}

// Timer emits a timer metric (duration as seconds).
func (mp *MetricsPipeline) Timer(name string, d time.Duration, labels map[string]string) {
	mp.emit("timer", name, d.Seconds(), labels)
}
