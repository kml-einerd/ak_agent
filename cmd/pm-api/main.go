package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/kml-einerd/ak-agent/pkg/api"
	"github.com/kml-einerd/ak-agent/pkg/engine"
)

func main() {
	apiKey := getenv("PM_API_KEY", "pmos_test_key_2024")
	port := getenv("PM_API_PORT", "8080")

	mp := engine.NewMetricsPipeline(stdoutFlusher, engine.WithFlushInterval(5*time.Second))
	defer mp.Stop()

	narrator := engine.NewNarratorLive(engine.WithNarratorMetrics(mp))
	defer narrator.Stop()

	store := engine.NewInMemoryRunStore()

	opts := append(narrator.Hooks(),
		engine.WithExecutor(engine.NewShellMoaExecutor()),
		engine.WithRunStore(store),
		engine.WithMaxParallelism(4),
	)
	e := engine.New(opts...)

	handler := api.NewServer(e, store, apiKey)

	srv := &http.Server{
		Addr:              ":" + port,
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		fmt.Printf("pm-api listening on :%s\n", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "listen error: %v\n", err)
			os.Exit(1)
		}
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	fmt.Println("shutting down")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		fmt.Fprintf(os.Stderr, "http shutdown: %v\n", err)
	}
	mp.Stop()
	narrator.Stop()
}

func getenv(k, fallback string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return fallback
}

func stdoutFlusher(events []engine.MetricEvent) error {
	for _, ev := range events {
		line, _ := json.Marshal(ev)
		fmt.Println(string(line))
	}
	return nil
}
