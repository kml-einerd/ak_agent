package engine

import (
	"runtime"
	"sync"
	"testing"
	"time"
)

func TestNarrator_DetectsStuckTask(t *testing.T) {
	n := NewNarratorLive()
	defer n.Stop()

	// Task started 6 minutes ago, still no completion — should be stuck
	n.OnTask(TaskResult{
		TaskID:   "task-1",
		WaveID:   "wave-1",
		RunID:    "run-1",
		Status:   "running",
		Duration: 6 * time.Minute,
	})

	alerts := n.Alerts("run-1")
	found := false
	for _, a := range alerts {
		if a.Kind == "stuck_task" && a.TaskID == "task-1" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected stuck_task alert for task-1, got alerts: %v", alerts)
	}
}

func TestNarrator_DetectsWaveFailure(t *testing.T) {
	n := NewNarratorLive()
	defer n.Stop()

	// All tasks in wave failed — 100% failure
	results := []TaskResult{
		{TaskID: "t1", WaveID: "w1", RunID: "r1", Status: "failed", Error: "boom"},
		{TaskID: "t2", WaveID: "w1", RunID: "r1", Status: "failed", Error: "crash"},
	}

	n.OnWave("w1", results)

	alerts := n.Alerts("r1")
	found := false
	for _, a := range alerts {
		if a.Kind == "wave_total_failure" && a.WaveID == "w1" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected wave_total_failure alert for w1, got alerts: %v", alerts)
	}
}

func TestNarrator_TracksCost(t *testing.T) {
	n := NewNarratorLive()
	defer n.Stop()

	// Run completed with cost 3.5x over budget
	n.OnRun(RunResult{
		RunID:       "r1",
		Status:      "success",
		TotalCost:   35.0,
		BudgetLimit: 10.0,
	})

	alerts := n.Alerts("r1")
	found := false
	for _, a := range alerts {
		if a.Kind == "cost_overrun" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected cost_overrun alert, got alerts: %v", alerts)
	}

	summary := n.Summary("r1")
	if summary == "" {
		t.Error("expected non-empty summary for completed run")
	}
}

func TestNarrator_ConcurrentSafe(t *testing.T) {
	n := NewNarratorLive()

	goroutinesBefore := runtime.NumGoroutine()

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(3)
		go func(i int) {
			defer wg.Done()
			n.OnTask(TaskResult{
				TaskID:   "task",
				WaveID:   "wave",
				RunID:    "run",
				Status:   "success",
				Duration: time.Duration(i) * time.Second,
				Cost:     float64(i) * 0.1,
			})
		}(i)
		go func() {
			defer wg.Done()
			n.OnWave("wave", []TaskResult{
				{TaskID: "t", WaveID: "wave", RunID: "run", Status: "success"},
			})
		}()
		go func() {
			defer wg.Done()
			_ = n.Alerts("run")
		}()
	}
	wg.Wait()

	// Stop narrator and verify goroutine cleanup (Keel: zero goroutines assertion)
	n.Stop()

	// Give goroutines time to exit
	time.Sleep(100 * time.Millisecond)

	goroutinesAfter := runtime.NumGoroutine()
	// Allow small delta for runtime goroutines, but narrator must not leak
	if goroutinesAfter > goroutinesBefore+2 {
		t.Errorf("goroutine leak: before=%d after=%d (delta > 2)", goroutinesBefore, goroutinesAfter)
	}
}
