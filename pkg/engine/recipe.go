package engine

import "fmt"

// Task descreve uma unidade de trabalho dentro de uma Recipe.
type Task struct {
	ID        string         `json:"id"`
	Type      string         `json:"type"`
	Args      map[string]any `json:"args,omitempty"`
	DependsOn []string       `json:"depends_on,omitempty"`
}

// Recipe e o payload que o cliente envia via POST /api/v2/run.
type Recipe struct {
	ID     string  `json:"id"`
	Tasks  []Task  `json:"tasks"`
	Budget float64 `json:"budget,omitempty"`
}

// topoWaves converte uma Recipe num slice de waves (cada wave e um slice de tasks
// que podem executar em paralelo). Detecta ciclos, dependencias ausentes e IDs
// duplicados.
func topoWaves(r Recipe) ([][]Task, error) {
	if len(r.Tasks) == 0 {
		return nil, nil
	}

	index := make(map[string]Task, len(r.Tasks))
	for _, t := range r.Tasks {
		if _, dup := index[t.ID]; dup {
			return nil, fmt.Errorf("duplicate task id %q", t.ID)
		}
		index[t.ID] = t
	}

	for _, t := range r.Tasks {
		for _, dep := range t.DependsOn {
			if _, ok := index[dep]; !ok {
				return nil, fmt.Errorf("task %q depends on missing task %q", t.ID, dep)
			}
		}
	}

	remaining := make(map[string]map[string]struct{}, len(r.Tasks))
	for _, t := range r.Tasks {
		set := make(map[string]struct{}, len(t.DependsOn))
		for _, d := range t.DependsOn {
			set[d] = struct{}{}
		}
		remaining[t.ID] = set
	}

	order := make(map[string]int, len(r.Tasks))
	for i, t := range r.Tasks {
		order[t.ID] = i
	}

	var waves [][]Task
	for len(remaining) > 0 {
		var ready []Task
		for id, deps := range remaining {
			if len(deps) == 0 {
				ready = append(ready, index[id])
			}
		}
		if len(ready) == 0 {
			var ids []string
			for id := range remaining {
				ids = append(ids, id)
			}
			return nil, fmt.Errorf("cycle detected among tasks %v", ids)
		}

		// ordem estavel: ordem de declaracao na recipe
		sortTasksByDeclOrder(ready, order)

		for _, t := range ready {
			delete(remaining, t.ID)
		}
		for _, deps := range remaining {
			for _, t := range ready {
				delete(deps, t.ID)
			}
		}
		waves = append(waves, ready)
	}

	return waves, nil
}

func sortTasksByDeclOrder(tasks []Task, order map[string]int) {
	for i := 1; i < len(tasks); i++ {
		for j := i; j > 0 && order[tasks[j].ID] < order[tasks[j-1].ID]; j-- {
			tasks[j], tasks[j-1] = tasks[j-1], tasks[j]
		}
	}
}
