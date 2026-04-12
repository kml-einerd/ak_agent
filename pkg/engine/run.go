package engine

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Run executa uma Recipe sincronamente. Para disparar em goroutine, envolva
// manualmente. Atualiza o RunStore (se configurado) a cada transicao.
func (e *Engine) Run(ctx context.Context, runID string, r Recipe) RunResult {
	result := RunResult{RunID: runID, BudgetLimit: r.Budget}

	if e.executor == nil {
		result.Status = "failed"
		result.Error = "engine has no executor configured"
		e.persistFinal(runID, result)
		e.FireAfterRun(result)
		return result
	}

	e.persistStart(runID)

	waves, err := topoWaves(r)
	if err != nil {
		result.Status = "failed"
		result.Error = err.Error()
		e.persistFinal(runID, result)
		e.FireAfterRun(result)
		return result
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	failed := false
	budgetExceeded := false

	for waveIdx, wave := range waves {
		waveID := fmt.Sprintf("w%d", waveIdx)
		results := e.dispatchWave(ctx, runID, waveID, wave)

		for i := range results {
			result.TotalCost += results[i].Cost
			if results[i].Status == "failed" {
				failed = true
			}
			e.FireAfterTask(results[i])
		}

		result.Waves = append(result.Waves, WaveResult{
			WaveID:  waveID,
			RunID:   runID,
			Results: results,
		})
		e.FireAfterWave(waveID, results)

		if r.Budget > 0 && result.TotalCost > r.Budget {
			budgetExceeded = true
			result.Error = fmt.Sprintf("budget exceeded: $%.2f > $%.2f", result.TotalCost, r.Budget)
			cancel()
			break
		}
		if failed {
			result.Error = "one or more tasks failed"
			cancel()
			break
		}
		if ctx.Err() != nil {
			result.Error = ctx.Err().Error()
			break
		}
	}

	switch {
	case budgetExceeded, failed, ctx.Err() != nil && result.Error == "":
		result.Status = "failed"
		if result.Error == "" && ctx.Err() != nil {
			result.Error = ctx.Err().Error()
		}
	default:
		result.Status = "success"
	}

	e.persistFinal(runID, result)
	e.FireAfterRun(result)
	return result
}

// dispatchWave executa uma wave com bounded parallelism.
func (e *Engine) dispatchWave(ctx context.Context, runID, waveID string, tasks []Task) []TaskResult {
	results := make([]TaskResult, len(tasks))
	sem := make(chan struct{}, e.maxParallelism)
	var wg sync.WaitGroup

	for i := range tasks {
		i := i
		task := tasks[i]
		wg.Add(1)
		go func() {
			defer wg.Done()
			select {
			case sem <- struct{}{}:
			case <-ctx.Done():
				results[i] = TaskResult{
					TaskID: task.ID,
					WaveID: waveID,
					RunID:  runID,
					Status: "failed",
					Error:  ctx.Err().Error(),
				}
				return
			}
			defer func() { <-sem }()

			res := e.executor.Execute(ctx, task)
			res.TaskID = task.ID
			res.WaveID = waveID
			res.RunID = runID
			if res.Status == "" {
				res.Status = "success"
			}
			results[i] = res
		}()
	}
	wg.Wait()
	return results
}

func (e *Engine) persistStart(runID string) {
	if e.store == nil {
		return
	}
	e.store.Update(runID, func(rec *RunRecord) {
		rec.Status = "running"
		if rec.StartedAt.IsZero() {
			rec.StartedAt = time.Now()
		}
	})
}

func (e *Engine) persistFinal(runID string, r RunResult) {
	if e.store == nil {
		return
	}
	end := time.Now()
	e.store.Update(runID, func(rec *RunRecord) {
		rec.Status = r.Status
		rec.EndedAt = &end
		cp := r
		rec.Result = &cp
		rec.Error = r.Error
	})
}
