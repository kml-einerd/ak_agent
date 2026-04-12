package api

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/kml-einerd/ak-agent/pkg/engine"
)

// NewServer monta o http.Handler com auth + rotas. Dispara runs em goroutines
// e retorna 202 com run_id imediato; o status real e consultado via GET.
func NewServer(e *engine.Engine, store engine.RunStore, apiKey string) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v2/run", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var body struct {
			RecipeInline engine.Recipe `json:"recipe_inline"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "invalid json", http.StatusBadRequest)
			return
		}
		if len(body.RecipeInline.Tasks) == 0 {
			http.Error(w, "recipe_inline.tasks must not be empty", http.StatusBadRequest)
			return
		}

		runID := newRunID()
		store.Create(runID)

		go func() {
			ctx := context.Background()
			e.Run(ctx, runID, body.RecipeInline)
		}()

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusAccepted)
		_ = json.NewEncoder(w).Encode(map[string]string{"run_id": runID})
	})

	mux.HandleFunc("/api/runs/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		id := strings.TrimPrefix(r.URL.Path, "/api/runs/")
		if id == "" {
			http.Error(w, "missing run id", http.StatusBadRequest)
			return
		}
		rec, ok := store.Get(id)
		if !ok {
			http.Error(w, "run not found", http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(rec)
	})

	return requireAPIKey(apiKey, mux)
}

func requireAPIKey(expected string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got := r.Header.Get("X-Api-Key")
		if expected == "" || got != expected {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func newRunID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		// fallback deterministico em caso improvavel
		return "run-err"
	}
	return hex.EncodeToString(b[:])
}
