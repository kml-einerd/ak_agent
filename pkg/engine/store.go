package engine

import (
	"sync"
	"time"
)

// RunRecord e o estado observavel de uma run (via GET /api/runs/{id}).
type RunRecord struct {
	ID        string     `json:"id"`
	Status    string     `json:"status"` // pending, running, success, failed
	StartedAt time.Time  `json:"started_at"`
	EndedAt   *time.Time `json:"ended_at,omitempty"`
	Result    *RunResult `json:"result,omitempty"`
	Error     string     `json:"error,omitempty"`
	Summary   string     `json:"summary,omitempty"`
}

// RunStore persiste RunRecords. Thread-safe.
type RunStore interface {
	Create(id string) *RunRecord
	Get(id string) (*RunRecord, bool)
	Update(id string, fn func(*RunRecord)) bool
}

// InMemoryRunStore e uma implementacao em memoria protegida por RWMutex.
type InMemoryRunStore struct {
	mu   sync.RWMutex
	runs map[string]*RunRecord
}

// NewInMemoryRunStore cria um store vazio.
func NewInMemoryRunStore() *InMemoryRunStore {
	return &InMemoryRunStore{runs: make(map[string]*RunRecord)}
}

// Create registra uma nova run. Retorna uma copia do record criado.
func (s *InMemoryRunStore) Create(id string) *RunRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec := &RunRecord{
		ID:        id,
		Status:    "pending",
		StartedAt: time.Now(),
	}
	s.runs[id] = rec
	c := *rec
	return &c
}

// Get retorna uma copia defensiva do record.
func (s *InMemoryRunStore) Get(id string) (*RunRecord, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	rec, ok := s.runs[id]
	if !ok {
		return nil, false
	}
	c := *rec
	return &c, true
}

// Update aplica fn sob write-lock.
func (s *InMemoryRunStore) Update(id string, fn func(*RunRecord)) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec, ok := s.runs[id]
	if !ok {
		return false
	}
	fn(rec)
	return true
}
