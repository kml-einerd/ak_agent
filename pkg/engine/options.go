package engine

// Option configures the Engine.
type Option func(*Engine)

// WithAfterTaskHook registers a hook called after each task completes.
func WithAfterTaskHook(h AfterTaskHook) Option {
	return func(e *Engine) {
		e.afterTaskHooks = append(e.afterTaskHooks, h)
	}
}

// WithAfterWaveHook registers a hook called after each wave completes.
func WithAfterWaveHook(h AfterWaveHook) Option {
	return func(e *Engine) {
		e.afterWaveHooks = append(e.afterWaveHooks, h)
	}
}

// WithAfterRunHook registers a hook called after a run completes.
func WithAfterRunHook(h AfterRunHook) Option {
	return func(e *Engine) {
		e.afterRunHooks = append(e.afterRunHooks, h)
	}
}

// WithExecutor injeta o Executor que o engine usa pra rodar tasks.
func WithExecutor(ex Executor) Option {
	return func(e *Engine) {
		e.executor = ex
	}
}

// WithRunStore injeta o RunStore usado pra registrar estado das runs.
func WithRunStore(s RunStore) Option {
	return func(e *Engine) {
		e.store = s
	}
}

// WithMaxParallelism limita quantas tasks rodam em paralelo dentro de uma wave.
func WithMaxParallelism(n int) Option {
	return func(e *Engine) {
		e.maxParallelism = n
	}
}
