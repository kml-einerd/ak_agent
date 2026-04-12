package engine

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"time"
)

// Executor roda uma Task. Implementacoes nao devem crashar o engine:
// falhas viram TaskResult.Status = "failed" com Error preenchido.
type Executor interface {
	Execute(ctx context.Context, t Task) TaskResult
}

// ShellMoaExecutor roda args["cmd"] via `sh -c` usando exec.CommandContext,
// de modo que cancelamento via ctx vira SIGKILL automatico.
type ShellMoaExecutor struct{}

// NewShellMoaExecutor constroi um ShellMoaExecutor.
func NewShellMoaExecutor() *ShellMoaExecutor {
	return &ShellMoaExecutor{}
}

// Execute implementa Executor.
func (s *ShellMoaExecutor) Execute(ctx context.Context, t Task) TaskResult {
	start := time.Now()
	res := TaskResult{TaskID: t.ID}

	cmdAny, ok := t.Args["cmd"]
	if !ok {
		res.Status = "failed"
		res.Error = "missing args.cmd"
		res.Duration = time.Since(start)
		return res
	}
	cmdStr, ok := cmdAny.(string)
	if !ok || cmdStr == "" {
		res.Status = "failed"
		res.Error = "args.cmd must be a non-empty string"
		res.Duration = time.Since(start)
		return res
	}

	cmd := exec.CommandContext(ctx, "sh", "-c", cmdStr)
	cmd.WaitDelay = 200 * time.Millisecond
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	res.Duration = time.Since(start)

	if err != nil {
		res.Status = "failed"
		if ctx.Err() != nil {
			res.Error = fmt.Sprintf("ctx: %v", ctx.Err())
		} else {
			msg := stderr.String()
			if msg == "" {
				msg = err.Error()
			}
			res.Error = msg
		}
		return res
	}

	res.Status = "success"
	return res
}

// StubExecutor permite testes deterministicos. Se Delay > 0, respeita ctx.
type StubExecutor struct {
	Results map[string]TaskResult
	Delay   time.Duration
}

// Execute implementa Executor retornando o TaskResult configurado (ou success vazio).
func (s *StubExecutor) Execute(ctx context.Context, t Task) TaskResult {
	if s.Delay > 0 {
		select {
		case <-ctx.Done():
			return TaskResult{TaskID: t.ID, Status: "failed", Error: "ctx cancelled"}
		case <-time.After(s.Delay):
		}
	}
	res, ok := s.Results[t.ID]
	if !ok {
		res = TaskResult{Status: "success"}
	}
	res.TaskID = t.ID
	return res
}
