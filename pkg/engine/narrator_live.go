package engine

import (
	"fmt"
	"sync"
	"time"
)

const stuckThreshold = 5 * time.Minute
const costOverrunMultiplier = 3.0

// Alert represents a narrator detection.
type Alert struct {
	Kind   string // "stuck_task", "wave_total_failure", "cost_overrun"
	RunID  string
	WaveID string
	TaskID string
	Msg    string
}

type runState struct {
	alerts  []Alert
	summary string
}

// NarratorLive observes engine lifecycle events and detects anomalies.
// Concurrent-safe via RWMutex. Runs a background goroutine for periodic checks.
type NarratorLive struct {
	mu   sync.RWMutex
	runs map[string]*runState
	done chan struct{}
	wg   sync.WaitGroup
}

// NewNarratorLive creates a NarratorLive and starts its background goroutine.
func NewNarratorLive() *NarratorLive {
	n := &NarratorLive{
		runs: make(map[string]*runState),
		done: make(chan struct{}),
	}
	n.wg.Add(1)
	go n.loop()
	return n
}

func (n *NarratorLive) loop() {
	defer n.wg.Done()
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-n.done:
			return
		case <-ticker.C:
			// periodic sweep placeholder
		}
	}
}

// Stop shuts down the background goroutine and waits for cleanup.
func (n *NarratorLive) Stop() {
	select {
	case <-n.done:
		return // already stopped
	default:
		close(n.done)
	}
	n.wg.Wait()
}

func (n *NarratorLive) getOrCreateRun(runID string) *runState {
	rs, ok := n.runs[runID]
	if !ok {
		rs = &runState{}
		n.runs[runID] = rs
	}
	return rs
}

// OnTask is called after each task completes. Detects stuck tasks (>5min).
func (n *NarratorLive) OnTask(r TaskResult) {
	n.mu.Lock()
	defer n.mu.Unlock()

	rs := n.getOrCreateRun(r.RunID)

	if r.Duration > stuckThreshold {
		rs.alerts = append(rs.alerts, Alert{
			Kind:   "stuck_task",
			RunID:  r.RunID,
			WaveID: r.WaveID,
			TaskID: r.TaskID,
			Msg:    fmt.Sprintf("task %s stuck for %s", r.TaskID, r.Duration),
		})
	}
}

// OnWave is called after all tasks in a wave complete. Detects 100% failure.
func (n *NarratorLive) OnWave(waveID string, results []TaskResult) {
	n.mu.Lock()
	defer n.mu.Unlock()

	if len(results) == 0 {
		return
	}

	runID := results[0].RunID
	rs := n.getOrCreateRun(runID)

	failed := 0
	for _, r := range results {
		if r.Status == "failed" {
			failed++
		}
	}

	if failed == len(results) {
		rs.alerts = append(rs.alerts, Alert{
			Kind:   "wave_total_failure",
			RunID:  runID,
			WaveID: waveID,
			Msg:    fmt.Sprintf("wave %s: all %d tasks failed", waveID, failed),
		})
	}
}

// OnRun is called after a run completes. Generates summary and detects cost overrun (>3x budget).
func (n *NarratorLive) OnRun(r RunResult) {
	n.mu.Lock()
	defer n.mu.Unlock()

	rs := n.getOrCreateRun(r.RunID)

	if r.BudgetLimit > 0 && r.TotalCost > r.BudgetLimit*costOverrunMultiplier {
		rs.alerts = append(rs.alerts, Alert{
			Kind:  "cost_overrun",
			RunID: r.RunID,
			Msg:   fmt.Sprintf("run %s cost $%.2f exceeds %.0fx budget $%.2f", r.RunID, r.TotalCost, costOverrunMultiplier, r.BudgetLimit),
		})
	}

	rs.summary = fmt.Sprintf("run %s: status=%s cost=$%.2f budget=$%.2f waves=%d",
		r.RunID, r.Status, r.TotalCost, r.BudgetLimit, len(r.Waves))
}

// Alerts returns all alerts for a run.
func (n *NarratorLive) Alerts(runID string) []Alert {
	n.mu.RLock()
	defer n.mu.RUnlock()

	rs, ok := n.runs[runID]
	if !ok {
		return nil
	}
	out := make([]Alert, len(rs.alerts))
	copy(out, rs.alerts)
	return out
}

// Summary returns the run summary.
func (n *NarratorLive) Summary(runID string) string {
	n.mu.RLock()
	defer n.mu.RUnlock()

	rs, ok := n.runs[runID]
	if !ok {
		return ""
	}
	return rs.summary
}

// Hooks returns engine options that wire the narrator into the engine.
func (n *NarratorLive) Hooks() []Option {
	return []Option{
		WithAfterTaskHook(n.OnTask),
		WithAfterWaveHook(n.OnWave),
		WithAfterRunHook(n.OnRun),
	}
}
