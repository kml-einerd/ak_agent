package engine

import "time"

// TaskResult is emitted after each task completes.
type TaskResult struct {
	TaskID   string
	WaveID   string
	RunID    string
	Status   string // "success", "failed"
	Duration time.Duration
	Cost     float64
	Error    string
}

// WaveResult is emitted after all tasks in a wave complete.
type WaveResult struct {
	WaveID  string
	RunID   string
	Results []TaskResult
}

// RunResult is emitted after an entire run completes.
type RunResult struct {
	RunID       string
	Status      string // "success", "failed", "partial"
	TotalCost   float64
	BudgetLimit float64
	Waves       []WaveResult
}

// Hook types — functions called at lifecycle points.
type AfterTaskHook func(TaskResult)
type AfterWaveHook func(string, []TaskResult) // waveID, results
type AfterRunHook func(RunResult)

// Engine orchestrates waves of parallel tasks.
type Engine struct {
	afterTaskHooks []AfterTaskHook
	afterWaveHooks []AfterWaveHook
	afterRunHooks  []AfterRunHook
}

// New creates an Engine with the given options.
func New(opts ...Option) *Engine {
	e := &Engine{}
	for _, opt := range opts {
		opt(e)
	}
	return e
}

// FireAfterTask calls all registered AfterTask hooks.
func (e *Engine) FireAfterTask(r TaskResult) {
	for _, h := range e.afterTaskHooks {
		h(r)
	}
}

// FireAfterWave calls all registered AfterWave hooks.
func (e *Engine) FireAfterWave(waveID string, results []TaskResult) {
	for _, h := range e.afterWaveHooks {
		h(waveID, results)
	}
}

// FireAfterRun calls all registered AfterRun hooks.
func (e *Engine) FireAfterRun(r RunResult) {
	for _, h := range e.afterRunHooks {
		h(r)
	}
}
