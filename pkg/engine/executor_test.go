package engine

import (
	"context"
	"strings"
	"testing"
	"time"
)

func TestShellMoaExecutor_Success(t *testing.T) {
	ex := NewShellMoaExecutor()
	task := Task{
		ID:   "echo-t",
		Type: "moa",
		Args: map[string]any{"cmd": "echo hello"},
	}
	res := ex.Execute(context.Background(), task)
	if res.Status != "success" {
		t.Fatalf("want success, got %s err=%s", res.Status, res.Error)
	}
	if res.TaskID != "echo-t" {
		t.Fatalf("taskID not set, got %q", res.TaskID)
	}
	if res.Duration <= 0 {
		t.Fatalf("duration must be > 0, got %v", res.Duration)
	}
}

func TestShellMoaExecutor_Failure(t *testing.T) {
	ex := NewShellMoaExecutor()
	task := Task{
		ID:   "fail-t",
		Type: "moa",
		Args: map[string]any{"cmd": "sh -c 'echo nope 1>&2; exit 2'"},
	}
	res := ex.Execute(context.Background(), task)
	if res.Status != "failed" {
		t.Fatalf("want failed, got %s", res.Status)
	}
	if res.Error == "" {
		t.Fatalf("want error populated")
	}
}

func TestShellMoaExecutor_MissingCmd(t *testing.T) {
	ex := NewShellMoaExecutor()
	res := ex.Execute(context.Background(), Task{ID: "x", Type: "moa"})
	if res.Status != "failed" {
		t.Fatalf("want failed for missing cmd, got %s", res.Status)
	}
	if !strings.Contains(res.Error, "cmd") {
		t.Fatalf("want cmd error, got %q", res.Error)
	}
}

func TestShellMoaExecutor_ContextCancel(t *testing.T) {
	ex := NewShellMoaExecutor()
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	task := Task{
		ID:   "sleep-t",
		Type: "moa",
		Args: map[string]any{"cmd": "sleep 5"},
	}
	start := time.Now()
	res := ex.Execute(ctx, task)
	if time.Since(start) > 2*time.Second {
		t.Fatalf("executor did not respect ctx cancel, took %v", time.Since(start))
	}
	if res.Status != "failed" {
		t.Fatalf("want failed on ctx cancel, got %s", res.Status)
	}
}

func TestStubExecutor_ReturnsConfigured(t *testing.T) {
	ex := &StubExecutor{
		Results: map[string]TaskResult{
			"t1": {Status: "success", Cost: 1.5},
		},
	}
	res := ex.Execute(context.Background(), Task{ID: "t1"})
	if res.Status != "success" || res.Cost != 1.5 {
		t.Fatalf("stub did not return configured result: %+v", res)
	}
	if res.TaskID != "t1" {
		t.Fatalf("stub must set TaskID, got %q", res.TaskID)
	}
}
