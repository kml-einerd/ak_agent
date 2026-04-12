package engine

import (
	"sync"
	"testing"
	"time"
)

func TestInMemoryRunStore_CreateGet(t *testing.T) {
	s := NewInMemoryRunStore()
	rec := s.Create("r1")
	if rec.ID != "r1" {
		t.Fatalf("want id r1, got %q", rec.ID)
	}
	if rec.Status != "pending" {
		t.Fatalf("want pending, got %s", rec.Status)
	}
	if rec.StartedAt.IsZero() {
		t.Fatalf("StartedAt must be set")
	}
	got, ok := s.Get("r1")
	if !ok || got.ID != "r1" {
		t.Fatalf("Get failed: %+v ok=%v", got, ok)
	}
}

func TestInMemoryRunStore_GetMissing(t *testing.T) {
	s := NewInMemoryRunStore()
	_, ok := s.Get("nope")
	if ok {
		t.Fatalf("must return ok=false for missing")
	}
}

func TestInMemoryRunStore_Update(t *testing.T) {
	s := NewInMemoryRunStore()
	s.Create("r1")
	ok := s.Update("r1", func(rec *RunRecord) {
		rec.Status = "running"
	})
	if !ok {
		t.Fatalf("update must succeed for existing")
	}
	got, _ := s.Get("r1")
	if got.Status != "running" {
		t.Fatalf("update did not persist, got %s", got.Status)
	}
}

func TestInMemoryRunStore_UpdateMissing(t *testing.T) {
	s := NewInMemoryRunStore()
	ok := s.Update("nope", func(rec *RunRecord) {})
	if ok {
		t.Fatalf("must return false for missing id")
	}
}

func TestInMemoryRunStore_GetReturnsCopy(t *testing.T) {
	s := NewInMemoryRunStore()
	s.Create("r1")
	s.Update("r1", func(rec *RunRecord) {
		rec.Status = "running"
	})
	got, _ := s.Get("r1")
	got.Status = "mutated"
	reread, _ := s.Get("r1")
	if reread.Status != "running" {
		t.Fatalf("store leaked internal pointer: status=%s", reread.Status)
	}
}

func TestInMemoryRunStore_ConcurrentAccess(t *testing.T) {
	s := NewInMemoryRunStore()
	s.Create("r1")

	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(2)
		go func() {
			defer wg.Done()
			s.Update("r1", func(rec *RunRecord) {
				rec.Status = "running"
				t := time.Now()
				rec.EndedAt = &t
			})
		}()
		go func() {
			defer wg.Done()
			_, _ = s.Get("r1")
		}()
	}
	wg.Wait()
}
