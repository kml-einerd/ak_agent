package engine

import (
	"context"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestEngineRun_LinearDAG(t *testing.T) {
	var taskHits int32
	e := New(
		WithExecutor(&StubExecutor{
			Results: map[string]TaskResult{
				"a": {Status: "success"},
				"b": {Status: "success"},
				"c": {Status: "success"},
			},
		}),
		WithAfterTaskHook(func(TaskResult) { atomic.AddInt32(&taskHits, 1) }),
	)
	r := Recipe{
		ID: "run-linear",
		Tasks: []Task{
			{ID: "a"},
			{ID: "b", DependsOn: []string{"a"}},
			{ID: "c", DependsOn: []string{"b"}},
		},
	}
	res := e.Run(context.Background(), "run-1", r)
	if res.Status != "success" {
		t.Fatalf("want success, got %s", res.Status)
	}
	if len(res.Waves) != 3 {
		t.Fatalf("want 3 waves, got %d", len(res.Waves))
	}
	if atomic.LoadInt32(&taskHits) != 3 {
		t.Fatalf("AfterTask hits want 3, got %d", taskHits)
	}
}

func TestEngineRun_ParallelWave(t *testing.T) {
	ex := &StubExecutor{
		Delay: 80 * time.Millisecond,
		Results: map[string]TaskResult{
			"a": {Status: "success"},
			"b": {Status: "success"},
			"c": {Status: "success"},
		},
	}
	e := New(WithExecutor(ex), WithMaxParallelism(4))
	r := Recipe{
		ID: "par",
		Tasks: []Task{
			{ID: "a"},
			{ID: "b"},
			{ID: "c"},
		},
	}
	start := time.Now()
	res := e.Run(context.Background(), "run-par", r)
	elapsed := time.Since(start)

	if res.Status != "success" {
		t.Fatalf("want success, got %s", res.Status)
	}
	if elapsed > 250*time.Millisecond {
		t.Fatalf("waves did not parallelize, elapsed=%v", elapsed)
	}
	if len(res.Waves) != 1 {
		t.Fatalf("want 1 wave (all parallel), got %d", len(res.Waves))
	}
}

func TestEngineRun_Failure(t *testing.T) {
	e := New(WithExecutor(&StubExecutor{
		Results: map[string]TaskResult{
			"a": {Status: "failed", Error: "boom"},
		},
	}))
	r := Recipe{ID: "fail", Tasks: []Task{{ID: "a"}}}
	res := e.Run(context.Background(), "run-f", r)
	if res.Status != "failed" {
		t.Fatalf("want failed, got %s", res.Status)
	}
}

func TestEngineRun_BudgetExceeded(t *testing.T) {
	e := New(WithExecutor(&StubExecutor{
		Results: map[string]TaskResult{
			"a": {Status: "success", Cost: 5.0},
			"b": {Status: "success", Cost: 5.0},
		},
	}))
	r := Recipe{
		ID:     "budget",
		Budget: 6.0,
		Tasks: []Task{
			{ID: "a"},
			{ID: "b", DependsOn: []string{"a"}},
		},
	}
	res := e.Run(context.Background(), "run-b", r)
	if res.Status != "failed" {
		t.Fatalf("want failed on budget, got %s", res.Status)
	}
	if res.TotalCost < 5.0 {
		t.Fatalf("cost must include completed task: got %v", res.TotalCost)
	}
}

func TestEngineRun_ContextCancel(t *testing.T) {
	ex := &StubExecutor{Delay: 2 * time.Second}
	e := New(WithExecutor(ex))
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		time.Sleep(50 * time.Millisecond)
		cancel()
	}()
	r := Recipe{ID: "cx", Tasks: []Task{
		{ID: "a"},
		{ID: "b", DependsOn: []string{"a"}},
	}}
	start := time.Now()
	res := e.Run(ctx, "run-cx", r)
	if time.Since(start) > 1500*time.Millisecond {
		t.Fatalf("run did not honor ctx cancel, elapsed=%v", time.Since(start))
	}
	if res.Status != "failed" {
		t.Fatalf("want failed, got %s", res.Status)
	}
}

func TestEngineRun_InvalidRecipe(t *testing.T) {
	e := New(WithExecutor(&StubExecutor{}))
	r := Recipe{ID: "bad", Tasks: []Task{
		{ID: "a", DependsOn: []string{"b"}},
		{ID: "b", DependsOn: []string{"a"}},
	}}
	res := e.Run(context.Background(), "run-bad", r)
	if res.Status != "failed" {
		t.Fatalf("want failed, got %s", res.Status)
	}
}

func TestEngineRun_StoreUpdated(t *testing.T) {
	store := NewInMemoryRunStore()
	e := New(
		WithExecutor(&StubExecutor{}),
		WithRunStore(store),
	)
	store.Create("run-store")
	r := Recipe{ID: "s", Tasks: []Task{{ID: "a"}}}
	e.Run(context.Background(), "run-store", r)
	rec, ok := store.Get("run-store")
	if !ok {
		t.Fatalf("record missing")
	}
	if rec.Status != "success" {
		t.Fatalf("store not updated, got %s", rec.Status)
	}
	if rec.Result == nil || len(rec.Result.Waves) != 1 {
		t.Fatalf("result not persisted: %+v", rec.Result)
	}
	if rec.EndedAt == nil {
		t.Fatalf("EndedAt missing")
	}
}

func TestEngineRun_NoExecutorFails(t *testing.T) {
	e := New()
	r := Recipe{ID: "ne", Tasks: []Task{{ID: "a"}}}
	res := e.Run(context.Background(), "run-ne", r)
	if res.Status != "failed" {
		t.Fatalf("want failed, got %s", res.Status)
	}
	if !strings.Contains(res.Error, "executor") {
		t.Fatalf("want executor error, got %q", res.Error)
	}
}
