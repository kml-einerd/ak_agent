package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/kml-einerd/ak-agent/pkg/engine"
)

const testAPIKey = "secret-test-key"

func newTestServer(t *testing.T, ex engine.Executor) (http.Handler, *engine.InMemoryRunStore, *engine.Engine) {
	t.Helper()
	store := engine.NewInMemoryRunStore()
	e := engine.New(
		engine.WithExecutor(ex),
		engine.WithRunStore(store),
	)
	h := NewServer(e, store, testAPIKey)
	return h, store, e
}

func postRun(t *testing.T, h http.Handler, key, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "/api/v2/run", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	if key != "" {
		req.Header.Set("X-Api-Key", key)
	}
	rr := httptest.NewRecorder()
	h.ServeHTTP(rr, req)
	return rr
}

func TestServer_AuthRequired(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	rr := postRun(t, h, "", `{"recipe_inline":{"id":"r","tasks":[{"id":"a"}]}}`)
	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", rr.Code)
	}
}

func TestServer_AuthWrong(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	rr := postRun(t, h, "nope", `{"recipe_inline":{"id":"r","tasks":[{"id":"a"}]}}`)
	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", rr.Code)
	}
}

func TestServer_BadPayload(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	rr := postRun(t, h, testAPIKey, "not json")
	if rr.Code != http.StatusBadRequest {
		t.Fatalf("want 400, got %d", rr.Code)
	}
}

func TestServer_EmptyTasks(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	rr := postRun(t, h, testAPIKey, `{"recipe_inline":{"id":"r","tasks":[]}}`)
	if rr.Code != http.StatusBadRequest {
		t.Fatalf("want 400 for empty tasks, got %d", rr.Code)
	}
}

func TestServer_AcceptsRunAndPolls(t *testing.T) {
	ex := &engine.StubExecutor{
		Delay: 30 * time.Millisecond,
		Results: map[string]engine.TaskResult{
			"a": {Status: "success", Cost: 1.0},
			"b": {Status: "success", Cost: 2.0},
		},
	}
	h, store, _ := newTestServer(t, ex)

	body := `{"recipe_inline":{"id":"r","tasks":[{"id":"a"},{"id":"b","depends_on":["a"]}]}}`
	rr := postRun(t, h, testAPIKey, body)
	if rr.Code != http.StatusAccepted {
		t.Fatalf("want 202, got %d body=%s", rr.Code, rr.Body.String())
	}
	var resp map[string]string
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatalf("bad json: %v", err)
	}
	runID := resp["run_id"]
	if runID == "" {
		t.Fatalf("no run_id returned")
	}
	if _, ok := store.Get(runID); !ok {
		t.Fatalf("store has no record for %s", runID)
	}

	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		req := httptest.NewRequest(http.MethodGet, "/api/runs/"+runID, nil)
		req.Header.Set("X-Api-Key", testAPIKey)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, req)
		if w.Code != http.StatusOK {
			t.Fatalf("GET want 200, got %d", w.Code)
		}
		var rec engine.RunRecord
		if err := json.Unmarshal(w.Body.Bytes(), &rec); err != nil {
			t.Fatalf("bad json: %v", err)
		}
		if rec.Status == "success" {
			if rec.Result == nil || len(rec.Result.Waves) != 2 {
				t.Fatalf("result not populated: %+v", rec.Result)
			}
			return
		}
		if rec.Status == "failed" {
			t.Fatalf("unexpected failure: %s", rec.Error)
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatalf("run did not finish in time")
}

func TestServer_GetMissing(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	req := httptest.NewRequest(http.MethodGet, "/api/runs/nope", nil)
	req.Header.Set("X-Api-Key", testAPIKey)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)
	if w.Code != http.StatusNotFound {
		t.Fatalf("want 404, got %d", w.Code)
	}
}

func TestServer_MethodNotAllowed(t *testing.T) {
	h, _, _ := newTestServer(t, &engine.StubExecutor{})
	req := httptest.NewRequest(http.MethodDelete, "/api/v2/run", strings.NewReader(""))
	req.Header.Set("X-Api-Key", testAPIKey)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)
	if w.Code != http.StatusMethodNotAllowed {
		t.Fatalf("want 405, got %d", w.Code)
	}
}
