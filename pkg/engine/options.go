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
