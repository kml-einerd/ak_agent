package engine

import (
	"strings"
	"testing"
)

func TestTopoWaves_LinearChain(t *testing.T) {
	r := Recipe{
		ID: "linear",
		Tasks: []Task{
			{ID: "a"},
			{ID: "b", DependsOn: []string{"a"}},
			{ID: "c", DependsOn: []string{"b"}},
		},
	}
	waves, err := topoWaves(r)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(waves) != 3 {
		t.Fatalf("want 3 waves, got %d", len(waves))
	}
	if waves[0][0].ID != "a" || waves[1][0].ID != "b" || waves[2][0].ID != "c" {
		t.Fatalf("unexpected wave order: %+v", waves)
	}
}

func TestTopoWaves_DiamondParallel(t *testing.T) {
	r := Recipe{
		ID: "diamond",
		Tasks: []Task{
			{ID: "a"},
			{ID: "b", DependsOn: []string{"a"}},
			{ID: "c", DependsOn: []string{"a"}},
			{ID: "d", DependsOn: []string{"b", "c"}},
		},
	}
	waves, err := topoWaves(r)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(waves) != 3 {
		t.Fatalf("want 3 waves, got %d: %+v", len(waves), waves)
	}
	if len(waves[1]) != 2 {
		t.Fatalf("wave[1] must be parallel b+c, got %+v", waves[1])
	}
	if waves[2][0].ID != "d" {
		t.Fatalf("last wave must be d")
	}
}

func TestTopoWaves_Cycle(t *testing.T) {
	r := Recipe{
		ID: "cycle",
		Tasks: []Task{
			{ID: "a", DependsOn: []string{"b"}},
			{ID: "b", DependsOn: []string{"a"}},
		},
	}
	_, err := topoWaves(r)
	if err == nil || !strings.Contains(err.Error(), "cycle") {
		t.Fatalf("want cycle error, got %v", err)
	}
}

func TestTopoWaves_MissingDependency(t *testing.T) {
	r := Recipe{
		ID: "missing",
		Tasks: []Task{
			{ID: "a", DependsOn: []string{"ghost"}},
		},
	}
	_, err := topoWaves(r)
	if err == nil || !strings.Contains(err.Error(), "ghost") {
		t.Fatalf("want missing-dep error mentioning ghost, got %v", err)
	}
}

func TestTopoWaves_EmptyRecipe(t *testing.T) {
	waves, err := topoWaves(Recipe{ID: "empty"})
	if err != nil {
		t.Fatalf("unexpected err: %v", err)
	}
	if len(waves) != 0 {
		t.Fatalf("want 0 waves, got %d", len(waves))
	}
}

func TestTopoWaves_DuplicateTaskID(t *testing.T) {
	r := Recipe{
		ID: "dup",
		Tasks: []Task{
			{ID: "a"},
			{ID: "a"},
		},
	}
	_, err := topoWaves(r)
	if err == nil || !strings.Contains(err.Error(), "duplicate") {
		t.Fatalf("want duplicate error, got %v", err)
	}
}
