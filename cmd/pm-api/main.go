package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/kml-einerd/ak-agent/pkg/engine"
)

func main() {
	narrator := engine.NewNarratorLive()
	defer narrator.Stop()

	e := engine.New(narrator.Hooks()...)

	_ = e // engine will be used when run loop is wired

	fmt.Println("pm-api ready")

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig

	fmt.Println("shutting down")
}
