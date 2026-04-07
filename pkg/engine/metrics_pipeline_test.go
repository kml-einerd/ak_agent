package engine

import (
	"runtime"
	"sync"
	"testing"
	"time"
)

func TestMetrics_ChannelPipeline(t *testing.T) {
	var flushed []MetricEvent
	var mu sync.Mutex

	flusher := func(batch []MetricEvent) error {
		mu.Lock()
		flushed = append(flushed, batch...)
		mu.Unlock()
		return nil
	}

	mp := NewMetricsPipeline(flusher, WithFlushInterval(50*time.Millisecond))
	defer mp.Stop()

	mp.Counter("tasks_completed", 1, map[string]string{"run": "r1"})
	mp.Gauge("active_tasks", 5, map[string]string{"wave": "w1"})
	mp.Timer("task_duration", 3*time.Second, map[string]string{"task": "t1"})

	// Wait for flush
	time.Sleep(150 * time.Millisecond)

	mu.Lock()
	defer mu.Unlock()

	if len(flushed) != 3 {
		t.Errorf("expected 3 events flushed, got %d", len(flushed))
	}

	kinds := map[string]bool{}
	for _, e := range flushed {
		kinds[e.Kind] = true
	}
	for _, want := range []string{"counter", "gauge", "timer"} {
		if !kinds[want] {
			t.Errorf("missing event kind %q in flushed events", want)
		}
	}
}

func TestMetrics_BatchFlush(t *testing.T) {
	flushCount := 0
	var mu sync.Mutex

	flusher := func(batch []MetricEvent) error {
		mu.Lock()
		flushCount++
		mu.Unlock()
		return nil
	}

	mp := NewMetricsPipeline(flusher, WithFlushInterval(50*time.Millisecond))
	defer mp.Stop()

	// Send events in two batches separated by flush interval
	mp.Counter("a", 1, nil)
	mp.Counter("b", 1, nil)

	time.Sleep(80 * time.Millisecond)

	mp.Counter("c", 1, nil)

	time.Sleep(80 * time.Millisecond)

	mu.Lock()
	defer mu.Unlock()

	if flushCount < 2 {
		t.Errorf("expected at least 2 flush calls, got %d", flushCount)
	}
}

func TestMetrics_RetryOnFlushError(t *testing.T) {
	attempts := 0
	var mu sync.Mutex

	flusher := func(batch []MetricEvent) error {
		mu.Lock()
		attempts++
		a := attempts
		mu.Unlock()
		if a <= 2 {
			return errFlushFailed
		}
		return nil
	}

	mp := NewMetricsPipeline(flusher,
		WithFlushInterval(50*time.Millisecond),
		WithMaxRetries(3),
	)
	defer mp.Stop()

	mp.Counter("x", 1, nil)

	// Wait for retries (50ms flush + backoff retries)
	time.Sleep(500 * time.Millisecond)

	mu.Lock()
	defer mu.Unlock()

	if attempts < 3 {
		t.Errorf("expected at least 3 attempts (2 failures + 1 success), got %d", attempts)
	}
}

func TestMetrics_GoroutineCleanup(t *testing.T) {
	goroutinesBefore := runtime.NumGoroutine()

	flusher := func(batch []MetricEvent) error { return nil }
	mp := NewMetricsPipeline(flusher, WithFlushInterval(50*time.Millisecond))

	// Send some events
	for i := 0; i < 50; i++ {
		mp.Counter("test", float64(i), nil)
	}

	// Stop BEFORE waiting for flush (Keel: cleanup before flush)
	mp.Stop()

	time.Sleep(100 * time.Millisecond)

	goroutinesAfter := runtime.NumGoroutine()
	if goroutinesAfter > goroutinesBefore+2 {
		t.Errorf("goroutine leak: before=%d after=%d (delta > 2)", goroutinesBefore, goroutinesAfter)
	}
}

func TestMetrics_NarratorIntegration(t *testing.T) {
	var flushed []MetricEvent
	var mu sync.Mutex

	flusher := func(batch []MetricEvent) error {
		mu.Lock()
		flushed = append(flushed, batch...)
		mu.Unlock()
		return nil
	}

	mp := NewMetricsPipeline(flusher, WithFlushInterval(50*time.Millisecond))
	defer mp.Stop()

	n := NewNarratorLive(WithNarratorMetrics(mp))
	defer n.Stop()

	n.OnTask(TaskResult{
		TaskID: "t1", WaveID: "w1", RunID: "r1",
		Status: "success", Duration: 2 * time.Second, Cost: 0.5,
	})

	n.OnRun(RunResult{
		RunID: "r1", Status: "success", TotalCost: 5.0, BudgetLimit: 10.0,
	})

	time.Sleep(150 * time.Millisecond)

	mu.Lock()
	defer mu.Unlock()

	if len(flushed) == 0 {
		t.Error("expected narrator to emit metrics, got none")
	}
}
