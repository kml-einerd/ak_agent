# BodyCam + Android Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um sistema de observabilidade total (BodyCam) que captura tudo que o agente Android vê, faz e comunica — integrado ao PM-OS com traces distribuídos, interceptação de rede, extensão de navegador e replay completo.

**Architecture:** O celular roda APENAS apps Android nativos (DroidRun Portal + PCAPdroid + screen recorder). O cérebro do agente roda no GCP como um novo serviço Cloud Run (pm-android-agent) que se comunica com o Portal via Tailscale/WebSocket. Toda observabilidade converge para BigQuery via OpenTelemetry + Cloud Logging sinks. O PM-OS existente recebe instrumentação via middleware + OTel SDK nos serviços Go. Uma extensão de navegador Chrome captura toda atividade web como sensor adicional.

**Tech Stack:**
- Go 1.25 (consistente com PM-OS)
- OpenTelemetry Go SDK (`go.opentelemetry.io/otel`)
- Google Cloud: Trace, Logging, BigQuery, Speech-to-Text, GCS
- DroidRun Portal API (HTTP :8080 / WebSocket :8081)
- PCAPdroid (Android, open source, VPN-based traffic capture)
- mitmproxy (auto-hospedado nesta máquina agdis)
- Chrome Extension (Manifest V3) para captura web
- Metabase (já em uso) para dashboards

**Recursos disponíveis:**
- Máquina agdis: dedicada ao agente, navegador, credenciais Google, email próprio
- Moto G04s: Tailscale conectado, pode instalar qualquer app/config
- 6-7 terminais Claude Code com waves paralelas
- GCP project circular-transport-pr8vp com APIs habilitadas (Speech-to-Text, Vertex AI, etc)

---

## Execução: 7 Terminais Paralelos via Wave Runner

Este plano é executado com o `wave-runner.py` — orquestrador que abre 7 terminais tmux, cada um com Claude Code --dangerously-skip-permissions.

**Comandos:**
```bash
cd /home/agdis/pm-os-gcp
./scripts/wave-runner.py launch        # Abre 7 terminais com Claude
./scripts/wave-runner.py inject a      # Injeta Wave A em todos
./scripts/wave-runner.py status        # Verifica progresso
./scripts/wave-runner.py inject b      # Injeta Wave B quando A terminar
./scripts/wave-runner.py inject c      # Injeta Wave C quando B terminar
./scripts/wave-runner.py review c      # Review final
./scripts/wave-runner.py kill          # Limpa tudo
```

**Alocação de Terminais (zero conflito de arquivo):**

| Terminal | Track | Arquivos Exclusivos | Wave A | Wave B | Wave C |
|----------|-------|---------------------|--------|--------|--------|
| T1 | Android Agent | pkg/android/, cmd/pm-android-agent/ | Portal Client + Types | Agent Service | Dockerfile + systemd |
| T2 | BodyCam Core | pkg/bodycam/ | Logger + Sinks | GCS + Audio + STT | Integrar no agent |
| T3 | Telemetry | pkg/telemetry/, pkg/logger/ | OTel Setup | HTTP Middleware | Log unificado + metrics |
| T4 | PM-API | cmd/pm-api/ | Testes integração | Add middleware + OTel | Health check |
| T5 | PM-Worker | cmd/pm-worker/, pkg/orchestration/pubsub.go | Testes integração | OTel spans + PubSub trace | Health check |
| T6 | Chrome Extension | extensions/ | Manifest + Scripts | Popup + Settings | Instalar na agdis |
| T7 | Infra + Network | scripts/bodycam/, cloudbuild.yaml | mitmproxy setup | BigQuery + Metabase | APK patch + deploy |

**Dependências entre terminais:**
- T4 Wave B depende de T3 Wave B (precisa do middleware)
- T5 Wave B depende de T3 Wave A (precisa do OTel init)
- T2 Wave C e T1 Wave C coordenam (endpoint no mesmo binary)

**Sync points:**
- Após Wave A: `git pull` em todos, resolve conflitos em go.mod/go.sum
- Após Wave B: merge + teste de integração coletivo
- Após Wave C: deploy + setup celular

**Config:** `scripts/wave-config.json`

---

## Extras Sinergéticos (incluídos nas waves)

1. **Log unificado** (T3 Wave C) — padronizar zerolog output pro mesmo schema JSON da bodycam
2. **LLM cost metrics** (T3 Wave C) — OTel counter pra custo/tokens, habilita alertas Cloud Monitoring
3. **Health check unificado** (T4+T5 Wave C) — cada serviço reporta status de dependências

---

## Subsistemas

Este plano cobre 7 subsistemas independentes que convergem no BigQuery:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BODYCAM SYSTEM                                  │
│                                                                         │
│  Sub 1: Android Agent Bridge (Go service → DroidRun Portal)            │
│  Sub 2: BodyCam Visual + Áudio (screenshots, screen rec, mic, STT)     │
│  Sub 3: BodyCam Rede (PCAPdroid + mitmproxy → HTTPS decriptado)        │
│  Sub 4: PM-OS Instrumentation (OpenTelemetry + middleware nos serviços) │
│  Sub 5: BodyCam Browser (Chrome Extension captura web activity)         │
│                                                                         │
│  Convergência: BigQuery ← Cloud Logging sink ← todos os subsistemas    │
│  Visualização: Metabase dashboards                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Sub 1: Android Agent Bridge

> Serviço Go no GCP que é o "cérebro" controlando o celular via DroidRun Portal.

### Task 1.1: DroidRun Portal Client (Go)

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/android/portal_client.go`
- Create: `/home/agdis/pm-os-gcp/pkg/android/portal_client_test.go`
- Create: `/home/agdis/pm-os-gcp/pkg/android/types.go`

- [ ] **Step 1: Write failing test — portal client ping**

```go
// portal_client_test.go
package android

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestPortalClient_Ping(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path != "/ping" {
            t.Errorf("expected /ping, got %s", r.URL.Path)
        }
        w.Write([]byte(`{"status":"success","result":"pong"}`))
    }))
    defer server.Close()

    client := NewPortalClient(server.URL, "test-token")
    err := client.Ping()
    if err != nil {
        t.Fatalf("ping failed: %v", err)
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -run TestPortalClient_Ping -v`
Expected: FAIL — `NewPortalClient` not defined

- [ ] **Step 3: Write types + portal client with Ping**

```go
// types.go
package android

// PortalResponse is the standard DroidRun Portal response format
type PortalResponse struct {
    Status string      `json:"status"`
    Result interface{} `json:"result,omitempty"`
    Error  string      `json:"error,omitempty"`
}

// PhoneState from /phone_state endpoint
type PhoneState struct {
    CurrentApp      string `json:"current_app"`
    FocusedElement  string `json:"focused_element"`
    KeyboardVisible bool   `json:"keyboard_visible"`
}

// A11yNode represents a UI element from accessibility tree
type A11yNode struct {
    Index       int    `json:"index"`
    Text        string `json:"text"`
    Class       string `json:"class"`
    Bounds      string `json:"bounds"`
    Clickable   bool   `json:"clickable"`
    Scrollable  bool   `json:"scrollable"`
    Editable    bool   `json:"editable"`
}
```

```go
// portal_client.go
package android

import (
    "encoding/base64"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "strings"
    "time"
)

type PortalClient struct {
    baseURL    string
    authToken  string
    httpClient *http.Client
}

func NewPortalClient(baseURL, authToken string) *PortalClient {
    return &PortalClient{
        baseURL:   strings.TrimRight(baseURL, "/"),
        authToken: authToken,
        httpClient: &http.Client{Timeout: 10 * time.Second},
    }
}

func (c *PortalClient) get(path string) (*PortalResponse, error) {
    req, err := http.NewRequest("GET", c.baseURL+path, nil)
    if err != nil {
        return nil, err
    }
    req.Header.Set("Authorization", "Bearer "+c.authToken)

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }

    var pr PortalResponse
    if err := json.Unmarshal(body, &pr); err != nil {
        return nil, fmt.Errorf("invalid response: %s", string(body))
    }
    if pr.Status == "error" {
        return nil, fmt.Errorf("portal error: %s", pr.Error)
    }
    return &pr, nil
}

func (c *PortalClient) post(path string, params url.Values) (*PortalResponse, error) {
    req, err := http.NewRequest("POST", c.baseURL+path, strings.NewReader(params.Encode()))
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    req.Header.Set("Authorization", "Bearer "+c.authToken)

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }

    var pr PortalResponse
    if err := json.Unmarshal(body, &pr); err != nil {
        return nil, fmt.Errorf("invalid response: %s", string(body))
    }
    if pr.Status == "error" {
        return nil, fmt.Errorf("portal error: %s", pr.Error)
    }
    return &pr, nil
}

func (c *PortalClient) Ping() error {
    _, err := c.get("/ping")
    return err
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -run TestPortalClient_Ping -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/android/portal_client.go pkg/android/portal_client_test.go pkg/android/types.go
git commit -m "feat(android): add DroidRun Portal client with ping"
```

### Task 1.2: Portal Client — UI Operations (screenshot, tree, tap, input)

**Files:**
- Modify: `/home/agdis/pm-os-gcp/pkg/android/portal_client.go`
- Modify: `/home/agdis/pm-os-gcp/pkg/android/portal_client_test.go`

- [ ] **Step 1: Write failing tests — GetA11yTree, GetPhoneState, InputText, PressKey**

```go
// portal_client_test.go (adicionar)

func TestPortalClient_GetA11yTree(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte(`{"status":"success","result":[{"index":0,"text":"WhatsApp","class":"TextView","clickable":true}]}`))
    }))
    defer server.Close()

    client := NewPortalClient(server.URL, "test-token")
    nodes, err := client.GetA11yTree()
    if err != nil {
        t.Fatalf("GetA11yTree failed: %v", err)
    }
    if len(nodes) != 1 {
        t.Fatalf("expected 1 node, got %d", len(nodes))
    }
    if nodes[0].Text != "WhatsApp" {
        t.Errorf("expected WhatsApp, got %s", nodes[0].Text)
    }
}

func TestPortalClient_GetPhoneState(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte(`{"status":"success","result":{"current_app":"com.whatsapp","focused_element":"","keyboard_visible":false}}`))
    }))
    defer server.Close()

    client := NewPortalClient(server.URL, "test-token")
    state, err := client.GetPhoneState()
    if err != nil {
        t.Fatalf("GetPhoneState failed: %v", err)
    }
    if state.CurrentApp != "com.whatsapp" {
        t.Errorf("expected com.whatsapp, got %s", state.CurrentApp)
    }
}

func TestPortalClient_InputText(t *testing.T) {
    var receivedB64 string
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        r.ParseForm()
        receivedB64 = r.FormValue("base64_text")
        w.Write([]byte(`{"status":"success","result":"ok"}`))
    }))
    defer server.Close()

    client := NewPortalClient(server.URL, "test-token")
    err := client.InputText("Hello World")
    if err != nil {
        t.Fatalf("InputText failed: %v", err)
    }

    decoded, _ := base64.StdEncoding.DecodeString(receivedB64)
    if string(decoded) != "Hello World" {
        t.Errorf("expected Hello World, got %s", string(decoded))
    }
}

func TestPortalClient_PressKey(t *testing.T) {
    var receivedCode string
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        r.ParseForm()
        receivedCode = r.FormValue("key_code")
        w.Write([]byte(`{"status":"success","result":"ok"}`))
    }))
    defer server.Close()

    client := NewPortalClient(server.URL, "test-token")
    err := client.PressKey(KeyEnter)
    if err != nil {
        t.Fatalf("PressKey failed: %v", err)
    }
    if receivedCode != "66" {
        t.Errorf("expected 66, got %s", receivedCode)
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -v`
Expected: FAIL — methods not defined

- [ ] **Step 3: Implement UI operations**

```go
// portal_client.go (adicionar)

// Key codes
const (
    KeyEnter     = 66
    KeyBackspace = 67
    KeyTab       = 61
    KeyEscape    = 111
    KeyHome      = 3
    KeyBack      = 4
)

func (c *PortalClient) GetA11yTree() ([]A11yNode, error) {
    pr, err := c.get("/a11y_tree")
    if err != nil {
        return nil, err
    }
    data, err := json.Marshal(pr.Result)
    if err != nil {
        return nil, err
    }
    var nodes []A11yNode
    return nodes, json.Unmarshal(data, &nodes)
}

func (c *PortalClient) GetPhoneState() (*PhoneState, error) {
    pr, err := c.get("/phone_state")
    if err != nil {
        return nil, err
    }
    data, err := json.Marshal(pr.Result)
    if err != nil {
        return nil, err
    }
    var state PhoneState
    return &state, json.Unmarshal(data, &state)
}

func (c *PortalClient) InputText(text string) error {
    encoded := base64.StdEncoding.EncodeToString([]byte(text))
    params := url.Values{"base64_text": {encoded}, "clear": {"true"}}
    _, err := c.post("/keyboard/input", params)
    return err
}

func (c *PortalClient) PressKey(keyCode int) error {
    params := url.Values{"key_code": {fmt.Sprintf("%d", keyCode)}}
    _, err := c.post("/keyboard/key", params)
    return err
}

func (c *PortalClient) GetInstalledApps() ([]string, error) {
    pr, err := c.get("/packages")
    if err != nil {
        return nil, err
    }
    data, err := json.Marshal(pr.Result)
    if err != nil {
        return nil, err
    }
    var apps []string
    return apps, json.Unmarshal(data, &apps)
}

func (c *PortalClient) GetFullState() (*PortalResponse, error) {
    return c.get("/state_full?filter=false")
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/android/
git commit -m "feat(android): portal client UI operations — tree, state, input, keys"
```

### Task 1.3: Android Agent Service (Cloud Run)

**Files:**
- Create: `/home/agdis/pm-os-gcp/cmd/pm-android-agent/main.go`
- Create: `/home/agdis/pm-os-gcp/pkg/android/agent.go`
- Create: `/home/agdis/pm-os-gcp/pkg/android/agent_test.go`

- [ ] **Step 1: Write failing test — agent receives task from PM-OS and executes on Portal**

```go
// agent_test.go
package android

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestAgent_ExecuteTask(t *testing.T) {
    var actions []string
    portal := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        actions = append(actions, r.URL.Path)
        switch r.URL.Path {
        case "/phone_state":
            w.Write([]byte(`{"status":"success","result":{"current_app":"com.android.launcher","keyboard_visible":false}}`))
        case "/a11y_tree":
            w.Write([]byte(`{"status":"success","result":[{"index":0,"text":"WhatsApp","clickable":true}]}`))
        default:
            w.Write([]byte(`{"status":"success","result":"ok"}`))
        }
    }))
    defer portal.Close()

    agent := NewAgent(NewPortalClient(portal.URL, "test"))
    result, err := agent.Execute(AgentTask{
        Action:  "get_screen_state",
        TaskID:  "test-001",
    })
    if err != nil {
        t.Fatalf("execute failed: %v", err)
    }
    if result.Status != "success" {
        t.Errorf("expected success, got %s", result.Status)
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -run TestAgent_ExecuteTask -v`
Expected: FAIL

- [ ] **Step 3: Implement Agent struct**

```go
// agent.go
package android

import (
    "fmt"
    "time"
)

type AgentTask struct {
    TaskID     string `json:"task_id"`
    Action     string `json:"action"`     // get_screen_state, tap, input_text, open_app, press_key
    Target     string `json:"target"`     // element text, app package, key name
    Text       string `json:"text"`       // for input_text
    RunID      string `json:"run_id"`     // PM-OS run correlation
}

type AgentResult struct {
    TaskID    string      `json:"task_id"`
    Status    string      `json:"status"` // success, error
    Data      interface{} `json:"data,omitempty"`
    Error     string      `json:"error,omitempty"`
    Duration  int64       `json:"duration_ms"`
    Timestamp time.Time   `json:"timestamp"`
}

type Agent struct {
    portal *PortalClient
}

func NewAgent(portal *PortalClient) *Agent {
    return &Agent{portal: portal}
}

func (a *Agent) Execute(task AgentTask) (*AgentResult, error) {
    start := time.Now()
    result := &AgentResult{
        TaskID:    task.TaskID,
        Timestamp: start,
    }

    var data interface{}
    var err error

    switch task.Action {
    case "get_screen_state":
        data, err = a.portal.GetFullState()
    case "get_phone_state":
        data, err = a.portal.GetPhoneState()
    case "get_tree":
        data, err = a.portal.GetA11yTree()
    case "input_text":
        err = a.portal.InputText(task.Text)
    case "press_key":
        keyCode := resolveKeyCode(task.Target)
        err = a.portal.PressKey(keyCode)
    case "get_apps":
        data, err = a.portal.GetInstalledApps()
    default:
        err = fmt.Errorf("unknown action: %s", task.Action)
    }

    result.Duration = time.Since(start).Milliseconds()
    if err != nil {
        result.Status = "error"
        result.Error = err.Error()
        return result, err
    }
    result.Status = "success"
    result.Data = data
    return result, nil
}

func resolveKeyCode(name string) int {
    codes := map[string]int{
        "enter": KeyEnter, "backspace": KeyBackspace,
        "tab": KeyTab, "escape": KeyEscape,
        "home": KeyHome, "back": KeyBack,
    }
    if code, ok := codes[name]; ok {
        return code
    }
    return 0
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/android/ -run TestAgent_ExecuteTask -v`
Expected: PASS

- [ ] **Step 5: Write the HTTP entry point**

```go
// cmd/pm-android-agent/main.go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"

    "pm-os-gcp/pkg/android"
    "pm-os-gcp/pkg/logger"
)

func main() {
    log := logger.New("android-agent")

    portalHost := os.Getenv("PORTAL_HOST") // e.g. "100.97.136.4:8080"
    portalToken := os.Getenv("PORTAL_TOKEN")
    if portalHost == "" {
        log.Fatal().Msg("PORTAL_HOST required")
    }

    portal := android.NewPortalClient("http://"+portalHost, portalToken)
    agent := android.NewAgent(portal)

    // Health check
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        err := portal.Ping()
        status := "ok"
        if err != nil {
            status = "portal_unreachable"
        }
        json.NewEncoder(w).Encode(map[string]string{"status": status})
    })

    // Execute task from PM-OS
    http.HandleFunc("/execute", func(w http.ResponseWriter, r *http.Request) {
        var task android.AgentTask
        if err := json.NewDecoder(r.Body).Decode(&task); err != nil {
            http.Error(w, err.Error(), 400)
            return
        }

        result, err := agent.Execute(task)
        if err != nil {
            log.Error().Err(err).Str("task_id", task.TaskID).Msg("task failed")
        } else {
            log.Info().Str("task_id", task.TaskID).Int64("duration_ms", result.Duration).Msg("task done")
        }

        json.NewEncoder(w).Encode(result)
    })

    port := os.Getenv("PORT")
    if port == "" {
        port = "8082"
    }
    log.Info().Str("port", port).Str("portal", portalHost).Msg("android agent starting")
    http.ListenAndServe(fmt.Sprintf(":%s", port), nil)
}
```

- [ ] **Step 6: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add cmd/pm-android-agent/ pkg/android/
git commit -m "feat(android): agent service — receives PM-OS tasks, executes on Portal"
```

---

## Sub 2: BodyCam Visual + Áudio

> Captura contínua do que o agente vê e ouve no celular.

### Task 2.1: BodyCam Event Logger

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/logger.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/logger_test.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/types.go`

- [ ] **Step 1: Write failing test — bodycam event creation and serialization**

```go
// logger_test.go
package bodycam

import (
    "encoding/json"
    "testing"
    "time"
)

func TestEvent_JSON(t *testing.T) {
    ev := Event{
        TraceID:   "trace-001",
        AgentID:   "android-01",
        DeviceID:  "moto-g04s",
        Timestamp: time.Date(2026, 3, 24, 14, 32, 15, 0, time.UTC),
        Layer:     LayerVisual,
        Type:      "screenshot",
        Data: map[string]interface{}{
            "screenshot_url": "gs://bodycam/2026/03/24/trace-001/screen-001.png",
            "ui_tree_nodes":  42,
        },
    }

    data, err := json.Marshal(ev)
    if err != nil {
        t.Fatal(err)
    }

    var parsed map[string]interface{}
    json.Unmarshal(data, &parsed)

    if parsed["layer"] != "visual" {
        t.Errorf("expected visual, got %v", parsed["layer"])
    }
    if parsed["trace_id"] != "trace-001" {
        t.Errorf("expected trace-001, got %v", parsed["trace_id"])
    }
}

func TestLogger_LogEvent(t *testing.T) {
    var captured []Event
    sink := func(ev Event) error {
        captured = append(captured, ev)
        return nil
    }

    logger := NewLogger("android-01", "moto-g04s", sink)
    logger.Log(LayerVisual, "screenshot", map[string]interface{}{"url": "test.png"})

    if len(captured) != 1 {
        t.Fatalf("expected 1 event, got %d", len(captured))
    }
    if captured[0].AgentID != "android-01" {
        t.Errorf("expected android-01, got %s", captured[0].AgentID)
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -v`
Expected: FAIL

- [ ] **Step 3: Implement types + logger**

```go
// types.go
package bodycam

import "time"

const (
    LayerVisual  = "visual"
    LayerNetwork = "network"
    LayerServer  = "server"
    LayerAudio   = "audio"
    LayerBrowser = "browser"
)

type Event struct {
    TraceID   string                 `json:"trace_id" bigquery:"trace_id"`
    AgentID   string                 `json:"agent_id" bigquery:"agent_id"`
    DeviceID  string                 `json:"device_id" bigquery:"device_id"`
    Timestamp time.Time              `json:"timestamp" bigquery:"timestamp"`
    Layer     string                 `json:"layer" bigquery:"layer"`
    Type      string                 `json:"type" bigquery:"type"`
    Data      map[string]interface{} `json:"data" bigquery:"data"`
}
```

```go
// logger.go
package bodycam

import (
    "sync"
    "time"

    "github.com/google/uuid"
)

type SinkFunc func(Event) error

type Logger struct {
    agentID  string
    deviceID string
    traceID  string
    sink     SinkFunc
    mu       sync.Mutex
}

func NewLogger(agentID, deviceID string, sink SinkFunc) *Logger {
    return &Logger{
        agentID:  agentID,
        deviceID: deviceID,
        traceID:  uuid.New().String(),
        sink:     sink,
    }
}

func (l *Logger) SetTraceID(id string) {
    l.mu.Lock()
    defer l.mu.Unlock()
    l.traceID = id
}

func (l *Logger) Log(layer, eventType string, data map[string]interface{}) error {
    l.mu.Lock()
    traceID := l.traceID
    l.mu.Unlock()

    ev := Event{
        TraceID:   traceID,
        AgentID:   l.agentID,
        DeviceID:  l.deviceID,
        Timestamp: time.Now().UTC(),
        Layer:     layer,
        Type:      eventType,
        Data:      data,
    }
    return l.sink(ev)
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/bodycam/
git commit -m "feat(bodycam): event types and logger with pluggable sinks"
```

### Task 2.2: BigQuery Sink + Cloud Logging Sink

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/sink_logging.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/sink_logging_test.go`

- [ ] **Step 1: Write failing test — Cloud Logging sink formats events correctly**

```go
// sink_logging_test.go
package bodycam

import (
    "encoding/json"
    "testing"
    "time"
)

func TestCloudLoggingSink_Format(t *testing.T) {
    ev := Event{
        TraceID:   "trace-001",
        AgentID:   "android-01",
        DeviceID:  "moto-g04s",
        Timestamp: time.Date(2026, 3, 24, 14, 0, 0, 0, time.UTC),
        Layer:     LayerVisual,
        Type:      "screenshot",
        Data:      map[string]interface{}{"url": "gs://test/img.png"},
    }

    entry := formatLogEntry(ev)
    var parsed map[string]interface{}
    json.Unmarshal(entry, &parsed)

    if parsed["severity"] != "INFO" {
        t.Errorf("expected INFO severity")
    }
    labels := parsed["labels"].(map[string]interface{})
    if labels["layer"] != "visual" {
        t.Errorf("expected visual layer label")
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -run TestCloudLoggingSink -v`
Expected: FAIL

- [ ] **Step 3: Implement Cloud Logging sink**

Cloud Logging no Cloud Run é automático — qualquer coisa impressa em stdout em formato JSON estruturado é capturada. O sink do BigQuery é configurado como log sink no GCP (infra, não código).

```go
// sink_logging.go
package bodycam

import (
    "encoding/json"
    "fmt"
    "os"
)

// formatLogEntry formats an Event as a Cloud Logging structured JSON entry.
// Cloud Run automatically ingests structured JSON from stdout.
func formatLogEntry(ev Event) []byte {
    entry := map[string]interface{}{
        "severity":  "INFO",
        "message":   fmt.Sprintf("bodycam:%s:%s", ev.Layer, ev.Type),
        "timestamp": ev.Timestamp.Format("2006-01-02T15:04:05.000Z"),
        "labels": map[string]string{
            "layer":    ev.Layer,
            "type":     ev.Type,
            "agent_id": ev.AgentID,
            "device_id": ev.DeviceID,
        },
        "trace_id": ev.TraceID,
        "bodycam":  ev.Data,
    }
    data, _ := json.Marshal(entry)
    return data
}

// NewCloudLoggingSink returns a SinkFunc that writes structured JSON to stdout.
// Cloud Run + Cloud Logging picks this up automatically.
// A BigQuery log sink routes entries with logName containing "bodycam" to the dataset.
func NewCloudLoggingSink() SinkFunc {
    return func(ev Event) error {
        entry := formatLogEntry(ev)
        _, err := fmt.Fprintln(os.Stdout, string(entry))
        return err
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -run TestCloudLoggingSink -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/bodycam/
git commit -m "feat(bodycam): Cloud Logging sink — auto-captured by Cloud Run, routable to BigQuery"
```

### Task 2.3: GCS Screenshot Upload

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/gcs_upload.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/gcs_upload_test.go`

- [ ] **Step 1: Write failing test — generates correct GCS path**

```go
// gcs_upload_test.go
package bodycam

import (
    "testing"
    "time"
)

func TestGCSPath(t *testing.T) {
    ts := time.Date(2026, 3, 24, 14, 32, 15, 0, time.UTC)
    path := gcsPath("bodycam-data", "trace-001", "screenshot", ts, ".png")
    expected := "bodycam-data/2026/03/24/trace-001/screenshot-143215.png"
    if path != expected {
        t.Errorf("expected %s, got %s", expected, path)
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement GCS uploader**

```go
// gcs_upload.go
package bodycam

import (
    "context"
    "fmt"
    "io"
    "time"

    "cloud.google.com/go/storage"
)

func gcsPath(bucket, traceID, eventType string, ts time.Time, ext string) string {
    return fmt.Sprintf("%s/%s/%s/%s-%s%s",
        bucket,
        ts.Format("2006/01/02"),
        traceID,
        eventType,
        ts.Format("150405"),
        ext,
    )
}

type GCSUploader struct {
    bucket string
    client *storage.Client
}

func NewGCSUploader(bucket string) (*GCSUploader, error) {
    client, err := storage.NewClient(context.Background())
    if err != nil {
        return nil, err
    }
    return &GCSUploader{bucket: bucket, client: client}, nil
}

func (u *GCSUploader) Upload(ctx context.Context, traceID, eventType string, data io.Reader, ext string) (string, error) {
    ts := time.Now().UTC()
    objectName := fmt.Sprintf("%s/%s/%s-%s%s",
        ts.Format("2006/01/02"),
        traceID,
        eventType,
        ts.Format("150405"),
        ext,
    )

    wc := u.client.Bucket(u.bucket).Object(objectName).NewWriter(ctx)
    if _, err := io.Copy(wc, data); err != nil {
        wc.Close()
        return "", err
    }
    if err := wc.Close(); err != nil {
        return "", err
    }

    return fmt.Sprintf("gs://%s/%s", u.bucket, objectName), nil
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -run TestGCSPath -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/bodycam/
git commit -m "feat(bodycam): GCS uploader for screenshots and media"
```

### Task 2.4: Audio Capture + Speech-to-Text Integration

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/audio.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/audio_test.go`

- [ ] **Step 1: Write failing test — audio chunk processing**

```go
// audio_test.go
package bodycam

import (
    "testing"
)

func TestAudioChunk_Metadata(t *testing.T) {
    chunk := AudioChunk{
        DeviceID:   "moto-g04s",
        TraceID:    "trace-001",
        DurationMs: 30000,
        Format:     "wav",
        SampleRate: 16000,
    }
    if chunk.DurationMs != 30000 {
        t.Errorf("expected 30000ms, got %d", chunk.DurationMs)
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement audio types + STT caller**

```go
// audio.go
package bodycam

import (
    "context"
    "fmt"
    "io"

    speech "cloud.google.com/go/speech/apiv1"
    speechpb "cloud.google.com/go/speech/apiv1/speechpb"
)

type AudioChunk struct {
    DeviceID   string `json:"device_id"`
    TraceID    string `json:"trace_id"`
    DurationMs int64  `json:"duration_ms"`
    Format     string `json:"format"` // wav, ogg, flac
    SampleRate int32  `json:"sample_rate"`
    GCSUri     string `json:"gcs_uri,omitempty"`
}

type Transcript struct {
    Text       string  `json:"text"`
    Confidence float32 `json:"confidence"`
    Language   string  `json:"language"`
}

type STTClient struct {
    client *speech.Client
    lang   string
}

func NewSTTClient(ctx context.Context, lang string) (*STTClient, error) {
    client, err := speech.NewClient(ctx)
    if err != nil {
        return nil, err
    }
    return &STTClient{client: client, lang: lang}, nil
}

func (s *STTClient) TranscribeFromGCS(ctx context.Context, gcsURI string, sampleRate int32) (*Transcript, error) {
    req := &speechpb.RecognizeRequest{
        Config: &speechpb.RecognitionConfig{
            Encoding:        speechpb.RecognitionConfig_LINEAR16,
            SampleRateHertz: sampleRate,
            LanguageCode:    s.lang,
        },
        Audio: &speechpb.RecognitionAudio{
            AudioSource: &speechpb.RecognitionAudio_Uri{Uri: gcsURI},
        },
    }

    resp, err := s.client.Recognize(ctx, req)
    if err != nil {
        return nil, fmt.Errorf("STT failed: %w", err)
    }

    if len(resp.Results) == 0 {
        return &Transcript{Text: "", Confidence: 0, Language: s.lang}, nil
    }

    best := resp.Results[0].Alternatives[0]
    return &Transcript{
        Text:       best.Transcript,
        Confidence: best.Confidence,
        Language:   s.lang,
    }, nil
}

// TranscribeFromReader reads audio bytes directly (for small chunks < 1min)
func (s *STTClient) TranscribeFromReader(ctx context.Context, audio io.Reader, sampleRate int32) (*Transcript, error) {
    data, err := io.ReadAll(audio)
    if err != nil {
        return nil, err
    }

    req := &speechpb.RecognizeRequest{
        Config: &speechpb.RecognitionConfig{
            Encoding:        speechpb.RecognitionConfig_LINEAR16,
            SampleRateHertz: sampleRate,
            LanguageCode:    s.lang,
        },
        Audio: &speechpb.RecognitionAudio{
            AudioSource: &speechpb.RecognitionAudio_Content{Content: data},
        },
    }

    resp, err := s.client.Recognize(ctx, req)
    if err != nil {
        return nil, fmt.Errorf("STT failed: %w", err)
    }

    if len(resp.Results) == 0 {
        return &Transcript{Text: "", Confidence: 0, Language: s.lang}, nil
    }

    best := resp.Results[0].Alternatives[0]
    return &Transcript{
        Text:       best.Transcript,
        Confidence: best.Confidence,
        Language:   s.lang,
    }, nil
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -run TestAudioChunk -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/bodycam/
git commit -m "feat(bodycam): audio capture types + Google Speech-to-Text integration"
```

---

## Sub 3: BodyCam Rede (Interceptação de Tráfego)

> mitmproxy auto-hospedado na máquina agdis + PCAPdroid no celular.

### Task 3.1: Setup mitmproxy na máquina agdis

**Files:**
- Create: `/home/agdis/pm-os-gcp/scripts/bodycam/mitmproxy-setup.sh`
- Create: `/home/agdis/pm-os-gcp/scripts/bodycam/mitmproxy-addon.py`

- [ ] **Step 1: Write the mitmproxy addon that logs all traffic as BodyCam events**

```python
# mitmproxy-addon.py
"""
mitmproxy addon that logs all HTTP/S traffic as structured JSON events.
Output goes to a JSONL file that a Go process reads and forwards to Cloud Logging.
"""
import json
import time
import os

OUTPUT_FILE = os.environ.get("BODYCAM_TRAFFIC_LOG", "/tmp/bodycam-traffic.jsonl")

class BodyCamTrafficLogger:
    def __init__(self):
        self.output = open(OUTPUT_FILE, "a")

    def response(self, flow):
        event = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "layer": "network",
            "type": "http_exchange",
            "data": {
                "request": {
                    "method": flow.request.method,
                    "url": flow.request.pretty_url,
                    "headers": dict(flow.request.headers),
                    "body_size": len(flow.request.content) if flow.request.content else 0,
                    "body_preview": (flow.request.content[:2000].decode("utf-8", errors="replace")
                                    if flow.request.content else ""),
                },
                "response": {
                    "status_code": flow.response.status_code,
                    "headers": dict(flow.response.headers),
                    "body_size": len(flow.response.content) if flow.response.content else 0,
                    "body_preview": (flow.response.content[:2000].decode("utf-8", errors="replace")
                                    if flow.response.content else ""),
                },
                "duration_ms": int((flow.response.timestamp_end - flow.request.timestamp_start) * 1000),
                "client_ip": flow.client_conn.peername[0] if flow.client_conn.peername else "",
            }
        }
        self.output.write(json.dumps(event) + "\n")
        self.output.flush()

addons = [BodyCamTrafficLogger()]
```

- [ ] **Step 2: Write the setup script**

```bash
#!/bin/bash
# mitmproxy-setup.sh
# Instala e configura mitmproxy na máquina agdis como proxy HTTPS transparente.
# O celular (PCAPdroid) aponta pra cá via Tailscale.

set -e

echo "=== BodyCam Network Layer — mitmproxy setup ==="

# 1. Instalar mitmproxy
if ! command -v mitmproxy &> /dev/null; then
    pip3 install mitmproxy
fi

# 2. Gerar certificados (primeira execução)
if [ ! -f ~/.mitmproxy/mitmproxy-ca-cert.pem ]; then
    echo "Gerando certificados CA..."
    mitmdump --set confdir=~/.mitmproxy -k &
    sleep 2
    kill %1 2>/dev/null || true
fi

# 3. Exportar cert pra instalar no celular
echo "Certificado CA disponível em:"
echo "  ~/.mitmproxy/mitmproxy-ca-cert.pem"
echo ""
echo "Instalar no celular:"
echo "  1. Copiar .pem pro celular"
echo "  2. Configurações → Segurança → Instalar certificado"
echo "  3. Ou: adb push ~/.mitmproxy/mitmproxy-ca-cert.pem /sdcard/"

# 4. Diretório de logs
mkdir -p /home/agdis/bodycam-logs

# 5. Criar systemd service pra rodar em background
sudo tee /etc/systemd/system/bodycam-proxy.service > /dev/null << 'UNIT'
[Unit]
Description=BodyCam mitmproxy — HTTPS traffic interceptor
After=network.target

[Service]
User=agdis
ExecStart=/usr/local/bin/mitmdump \
    --mode regular \
    --listen-port 8888 \
    --set confdir=/home/agdis/.mitmproxy \
    -s /home/agdis/pm-os-gcp/scripts/bodycam/mitmproxy-addon.py \
    -k
Restart=always
Environment=BODYCAM_TRAFFIC_LOG=/home/agdis/bodycam-logs/traffic.jsonl

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable bodycam-proxy
sudo systemctl start bodycam-proxy

echo "=== mitmproxy rodando na porta 8888 ==="
echo "Configure o celular (PCAPdroid) para apontar proxy SOCKS/HTTP em:"
echo "  $(tailscale ip -4):8888"
```

- [ ] **Step 3: Run setup**

Run: `bash /home/agdis/pm-os-gcp/scripts/bodycam/mitmproxy-setup.sh`
Expected: mitmproxy running, systemd service active

- [ ] **Step 4: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add scripts/bodycam/
git commit -m "feat(bodycam): mitmproxy setup — network traffic interceptor with JSONL logging"
```

### Task 3.2: Traffic Log Forwarder (JSONL → Cloud Logging)

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/traffic_forwarder.go`
- Create: `/home/agdis/pm-os-gcp/pkg/bodycam/traffic_forwarder_test.go`

- [ ] **Step 1: Write failing test — parse JSONL traffic line**

```go
// traffic_forwarder_test.go
package bodycam

import (
    "testing"
)

func TestParseTrafficLine(t *testing.T) {
    line := `{"timestamp":"2026-03-24T14:32:15.000Z","layer":"network","type":"http_exchange","data":{"request":{"method":"POST","url":"https://i.instagram.com/api/v1/media/like/"},"response":{"status_code":200},"duration_ms":45}}`

    ev, err := parseTrafficLine(line)
    if err != nil {
        t.Fatal(err)
    }
    if ev.Layer != "network" {
        t.Errorf("expected network, got %s", ev.Layer)
    }
    if ev.Type != "http_exchange" {
        t.Errorf("expected http_exchange, got %s", ev.Type)
    }
    data := ev.Data
    req := data["request"].(map[string]interface{})
    if req["method"] != "POST" {
        t.Errorf("expected POST, got %v", req["method"])
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement traffic line parser + tail forwarder**

```go
// traffic_forwarder.go
package bodycam

import (
    "bufio"
    "encoding/json"
    "io"
    "os"
    "time"
)

func parseTrafficLine(line string) (*Event, error) {
    var raw struct {
        Timestamp string                 `json:"timestamp"`
        Layer     string                 `json:"layer"`
        Type      string                 `json:"type"`
        Data      map[string]interface{} `json:"data"`
    }
    if err := json.Unmarshal([]byte(line), &raw); err != nil {
        return nil, err
    }

    ts, _ := time.Parse("2006-01-02T15:04:05.000Z", raw.Timestamp)

    return &Event{
        Timestamp: ts,
        Layer:     raw.Layer,
        Type:      raw.Type,
        Data:      raw.Data,
    }, nil
}

// TailAndForward tails a JSONL file and forwards each line to the sink.
// Runs indefinitely — call in a goroutine.
func TailAndForward(filePath string, sink SinkFunc, agentID, deviceID string) error {
    f, err := os.Open(filePath)
    if err != nil {
        return err
    }
    defer f.Close()

    // Seek to end — only forward new lines
    f.Seek(0, io.SeekEnd)

    scanner := bufio.NewScanner(f)
    for {
        for scanner.Scan() {
            line := scanner.Text()
            ev, err := parseTrafficLine(line)
            if err != nil {
                continue
            }
            ev.AgentID = agentID
            ev.DeviceID = deviceID
            sink(*ev)
        }
        // No new lines — wait briefly then retry
        time.Sleep(500 * time.Millisecond)
        // Reset scanner for new data
        scanner = bufio.NewScanner(f)
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/bodycam/ -run TestParseTrafficLine -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/bodycam/
git commit -m "feat(bodycam): traffic JSONL forwarder — tails mitmproxy output to Cloud Logging"
```

### Task 3.3: Certificate Pinning Bypass (apk-mitm)

**Files:**
- Create: `/home/agdis/pm-os-gcp/scripts/bodycam/patch-apk.sh`

- [ ] **Step 1: Write the APK patching script**

```bash
#!/bin/bash
# patch-apk.sh — Remove certificate pinning de APKs pra mitmproxy funcionar
# Uso: ./patch-apk.sh <app-package-name>
# Ex:  ./patch-apk.sh com.instagram.android
#      ./patch-apk.sh com.whatsapp

set -e

PKG="${1:?Uso: ./patch-apk.sh <package-name>}"
WORK_DIR="/home/agdis/bodycam-apks"
mkdir -p "$WORK_DIR"

echo "=== Patching $PKG ==="

# 1. Instalar apk-mitm se necessário
if ! command -v apk-mitm &> /dev/null; then
    npm install -g apk-mitm
fi

# 2. Baixar APK do celular via ADB (ou de APKPure/APKMirror)
echo "Opção 1: Extrair do celular via adb"
echo "  adb shell pm path $PKG"
echo "  adb pull <path> $WORK_DIR/$PKG.apk"
echo ""
echo "Opção 2: Baixar de apkpure.com/apkmirror.com"
echo ""

if [ ! -f "$WORK_DIR/$PKG.apk" ]; then
    echo "Coloque o APK em $WORK_DIR/$PKG.apk e rode novamente"
    exit 1
fi

# 3. Patch — remove certificate pinning
apk-mitm "$WORK_DIR/$PKG.apk" -o "$WORK_DIR/${PKG}-patched.apk"

echo ""
echo "=== APK patched ==="
echo "Instalar no celular:"
echo "  adb install -r $WORK_DIR/${PKG}-patched.apk"
echo ""
echo "Ou via SCP + Termux:"
echo "  scp -P 8022 $WORK_DIR/${PKG}-patched.apk 100.97.136.4:~/"
echo "  # No Termux: pm install ~/${PKG}-patched.apk"
```

- [ ] **Step 2: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add scripts/bodycam/patch-apk.sh
git commit -m "feat(bodycam): APK certificate pinning bypass script"
```

---

## Sub 4: PM-OS Instrumentation (OpenTelemetry)

> Instrumentar os serviços Go existentes com traces distribuídos e middleware de logging.

### Task 4.1: OpenTelemetry Setup Package

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/telemetry/otel.go`
- Create: `/home/agdis/pm-os-gcp/pkg/telemetry/otel_test.go`

- [ ] **Step 1: Add OpenTelemetry dependencies**

```bash
cd /home/agdis/pm-os-gcp
go get go.opentelemetry.io/otel@latest
go get go.opentelemetry.io/otel/sdk/trace@latest
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp@latest
go get github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/trace@latest
```

- [ ] **Step 2: Write failing test — tracer creation**

```go
// otel_test.go
package telemetry

import (
    "context"
    "testing"
)

func TestInitTracer(t *testing.T) {
    shutdown, err := InitTracer(context.Background(), "test-service", "test-project", true)
    if err != nil {
        t.Fatalf("InitTracer failed: %v", err)
    }
    defer shutdown(context.Background())

    tracer := Tracer("test")
    _, span := tracer.Start(context.Background(), "test-operation")
    span.End()
}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/telemetry/ -run TestInitTracer -v`
Expected: FAIL

- [ ] **Step 4: Implement OTel initialization**

```go
// otel.go
package telemetry

import (
    "context"
    "fmt"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
    "go.opentelemetry.io/otel/trace"

    cloudtrace "github.com/GoogleCloudPlatform/opentelemetry-operations-go/exporter/trace"
)

// InitTracer sets up OpenTelemetry with Google Cloud Trace exporter.
// If localDev is true, uses stdout exporter instead.
// Returns a shutdown function that must be called on exit.
func InitTracer(ctx context.Context, serviceName, gcpProjectID string, localDev bool) (func(context.Context) error, error) {
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName(serviceName),
            attribute.String("gcp.project_id", gcpProjectID),
        ),
    )
    if err != nil {
        return nil, fmt.Errorf("resource: %w", err)
    }

    var exporter sdktrace.SpanExporter
    if localDev {
        // In-memory exporter for tests
        exporter = &noopExporter{}
    } else {
        exporter, err = cloudtrace.New(cloudtrace.WithProjectID(gcpProjectID))
        if err != nil {
            return nil, fmt.Errorf("cloud trace exporter: %w", err)
        }
    }

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )
    otel.SetTracerProvider(tp)

    return tp.Shutdown, nil
}

// Tracer returns a named tracer from the global provider.
func Tracer(name string) trace.Tracer {
    return otel.Tracer("pm-os." + name)
}

// noopExporter is a no-op exporter for testing.
type noopExporter struct{}

func (e *noopExporter) ExportSpans(ctx context.Context, spans []sdktrace.ReadOnlySpan) error {
    return nil
}
func (e *noopExporter) Shutdown(ctx context.Context) error { return nil }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/telemetry/ -run TestInitTracer -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/telemetry/ go.mod go.sum
git commit -m "feat(telemetry): OpenTelemetry setup with Google Cloud Trace exporter"
```

### Task 4.2: BodyCam HTTP Middleware

**Files:**
- Create: `/home/agdis/pm-os-gcp/pkg/telemetry/middleware.go`
- Create: `/home/agdis/pm-os-gcp/pkg/telemetry/middleware_test.go`

- [ ] **Step 1: Write failing test — middleware captures request/response**

```go
// middleware_test.go
package telemetry

import (
    "bytes"
    "encoding/json"
    "io"
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestBodyCamMiddleware(t *testing.T) {
    var captured []map[string]interface{}

    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(200)
        w.Write([]byte(`{"result":"ok"}`))
    })

    mw := BodyCamMiddleware(handler, func(entry map[string]interface{}) {
        captured = append(captured, entry)
    })

    body := bytes.NewBufferString(`{"intent":"process leads"}`)
    req := httptest.NewRequest("POST", "/api/orchestrate", body)
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    mw.ServeHTTP(rec, req)

    if len(captured) != 1 {
        t.Fatalf("expected 1 captured entry, got %d", len(captured))
    }

    entry := captured[0]
    if entry["method"] != "POST" {
        t.Errorf("expected POST, got %v", entry["method"])
    }
    if entry["path"] != "/api/orchestrate" {
        t.Errorf("expected /api/orchestrate, got %v", entry["path"])
    }
    if entry["status"].(float64) != 200 {
        t.Errorf("expected 200, got %v", entry["status"])
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement middleware**

```go
// middleware.go
package telemetry

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
)

type LogFunc func(entry map[string]interface{})

// responseRecorder wraps http.ResponseWriter to capture status and body.
type responseRecorder struct {
    http.ResponseWriter
    status int
    body   bytes.Buffer
}

func (r *responseRecorder) WriteHeader(code int) {
    r.status = code
    r.ResponseWriter.WriteHeader(code)
}

func (r *responseRecorder) Write(b []byte) (int, error) {
    r.body.Write(b)
    return r.ResponseWriter.Write(b)
}

// BodyCamMiddleware captures every HTTP request/response with full payloads.
// logFn receives structured entries. If nil, writes JSON to stdout (Cloud Logging).
func BodyCamMiddleware(next http.Handler, logFn LogFunc) http.Handler {
    if logFn == nil {
        logFn = func(entry map[string]interface{}) {
            data, _ := json.Marshal(entry)
            fmt.Fprintln(os.Stdout, string(data))
        }
    }

    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Read and restore request body
        var reqBody string
        if r.Body != nil {
            bodyBytes, _ := io.ReadAll(r.Body)
            reqBody = string(bodyBytes)
            if len(reqBody) > 4000 {
                reqBody = reqBody[:4000] + "...[truncated]"
            }
            r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))
        }

        // OTel span
        tracer := otel.Tracer("pm-os.http")
        ctx, span := tracer.Start(r.Context(), fmt.Sprintf("%s %s", r.Method, r.URL.Path))
        defer span.End()

        span.SetAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("http.path", r.URL.Path),
        )

        // Capture response
        rec := &responseRecorder{ResponseWriter: w, status: 200}
        next.ServeHTTP(rec, r.WithContext(ctx))

        duration := time.Since(start)
        span.SetAttributes(
            attribute.Int("http.status_code", rec.status),
            attribute.Int64("http.duration_ms", duration.Milliseconds()),
        )

        respBody := rec.body.String()
        if len(respBody) > 4000 {
            respBody = respBody[:4000] + "...[truncated]"
        }

        entry := map[string]interface{}{
            "severity":     "INFO",
            "message":      fmt.Sprintf("bodycam:server:http %s %s → %d (%dms)", r.Method, r.URL.Path, rec.status, duration.Milliseconds()),
            "timestamp":    start.UTC().Format("2006-01-02T15:04:05.000Z"),
            "trace_id":     span.SpanContext().TraceID().String(),
            "span_id":      span.SpanContext().SpanID().String(),
            "method":       r.Method,
            "path":         r.URL.Path,
            "status":       float64(rec.status),
            "duration_ms":  duration.Milliseconds(),
            "request_body": reqBody,
            "response_body": respBody,
            "labels": map[string]string{
                "layer": "server",
                "type":  "http_exchange",
            },
        }
        logFn(entry)
    })
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/telemetry/ -run TestBodyCamMiddleware -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/telemetry/
git commit -m "feat(telemetry): BodyCam HTTP middleware — captures all requests/responses with OTel traces"
```

### Task 4.3: Instrument pm-api (add middleware + OTel init)

**Files:**
- Modify: `/home/agdis/pm-os-gcp/cmd/pm-api/main.go`

- [ ] **Step 1: Add OTel init at startup (before route registration)**

Add after existing setup code, before `http.ListenAndServe`:

```go
// OpenTelemetry initialization
import "pm-os-gcp/pkg/telemetry"

// In main():
shutdownTracer, err := telemetry.InitTracer(
    context.Background(),
    "pm-api",
    os.Getenv("GCP_PROJECT_ID"),
    os.Getenv("GCP_PROJECT_ID") == "", // localDev if no project ID
)
if err != nil {
    log.Warn().Err(err).Msg("OTel init failed — continuing without tracing")
} else {
    defer shutdownTracer(context.Background())
}
```

- [ ] **Step 2: Wrap the mux with BodyCam middleware**

Replace the `http.ListenAndServe(":"+port, mux)` call with:

```go
handler := telemetry.BodyCamMiddleware(mux, nil) // nil = stdout/Cloud Logging
http.ListenAndServe(":"+port, handler)
```

- [ ] **Step 3: Run existing tests to verify nothing broke**

Run: `cd /home/agdis/pm-os-gcp && go test ./cmd/pm-api/ -v -timeout 30s`
Expected: PASS (or no tests — verify manually)

- [ ] **Step 4: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add cmd/pm-api/main.go
git commit -m "feat(pm-api): add BodyCam middleware + OpenTelemetry tracing"
```

### Task 4.4: Instrument pm-worker (trace Claude CLI calls + third-party interactions)

**Files:**
- Modify: `/home/agdis/pm-os-gcp/cmd/pm-worker/main.go`

- [ ] **Step 1: Add OTel init at worker startup**

Same pattern as pm-api — add at top of `main()`:

```go
import "pm-os-gcp/pkg/telemetry"

shutdownTracer, _ := telemetry.InitTracer(
    context.Background(),
    "pm-worker",
    os.Getenv("GCP_PROJECT_ID"),
    os.Getenv("GCP_PROJECT_ID") == "",
)
defer shutdownTracer(context.Background())
```

- [ ] **Step 2: Add spans around Claude CLI execution**

In the function that calls Claude CLI, wrap with:

```go
tracer := telemetry.Tracer("worker")
ctx, span := tracer.Start(ctx, "claude_cli_execute")
span.SetAttributes(
    attribute.String("task.id", task.TaskID),
    attribute.String("task.type", task.Type),
    attribute.String("task.agent", task.Agent),
    attribute.String("llm.provider", task.Provider),
    attribute.String("llm.brain", task.Brain),
    attribute.String("run.id", task.RunID),
)
defer span.End()

// After execution completes:
span.SetAttributes(
    attribute.Float64("llm.cost_usd", cost),
    attribute.Int("llm.tokens_in", tokensIn),
    attribute.Int("llm.tokens_out", tokensOut),
    attribute.Int64("llm.duration_ms", duration),
    attribute.String("llm.session_id", sessionID),
    attribute.String("task.status", status),
)
```

- [ ] **Step 3: Add spans around result callback to pm-api**

Wrap the POST to `/api/tasks/{id}/result`:

```go
_, callbackSpan := tracer.Start(ctx, "callback_result")
callbackSpan.SetAttributes(
    attribute.String("task.id", task.TaskID),
    attribute.String("callback.url", apiURL),
    attribute.String("task.status", status),
)
// ... do the POST ...
callbackSpan.End()
```

- [ ] **Step 4: Run existing tests**

Run: `cd /home/agdis/pm-os-gcp && go test ./cmd/pm-worker/ -v -timeout 30s`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add cmd/pm-worker/main.go
git commit -m "feat(pm-worker): add OTel tracing — Claude CLI calls, task lifecycle, callbacks"
```

### Task 4.5: Instrument Pub/Sub Dispatcher (trace propagation between services)

**Files:**
- Modify: `/home/agdis/pm-os-gcp/pkg/orchestration/pubsub.go`

- [ ] **Step 1: Inject trace context into Pub/Sub message attributes**

```go
import (
    "pm-os-gcp/pkg/telemetry"
    "go.opentelemetry.io/otel/propagation"
)

// In PublishTask():
tracer := telemetry.Tracer("pubsub")
ctx, span := tracer.Start(ctx, "pubsub_publish")
span.SetAttributes(
    attribute.String("task.id", task.ID),
    attribute.String("pubsub.topic", d.topicID),
)
defer span.End()

// Inject trace context into Pub/Sub message attributes
carrier := propagation.MapCarrier{}
otel.GetTextMapPropagator().Inject(ctx, carrier)
// Add carrier values as Pub/Sub message attributes
```

- [ ] **Step 2: Extract trace context in worker when receiving Pub/Sub message**

```go
// In pm-worker /execute handler:
// Extract trace context from Pub/Sub message attributes
carrier := propagation.MapCarrier(msg.Attributes)
ctx = otel.GetTextMapPropagator().Extract(context.Background(), carrier)
// Now all spans in the worker are children of the pm-api span
```

- [ ] **Step 3: Run orchestration tests**

Run: `cd /home/agdis/pm-os-gcp && go test ./pkg/orchestration/ -v -timeout 120s`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add pkg/orchestration/pubsub.go
git commit -m "feat(telemetry): trace propagation through Pub/Sub — end-to-end trace from api to worker"
```

---

## Sub 5: BodyCam Browser (Chrome Extension)

> Extensão Chrome que captura toda atividade web como sensor adicional.

### Task 5.1: Chrome Extension — Manifest + Background Service Worker

**Files:**
- Create: `/home/agdis/pm-os-gcp/extensions/bodycam-browser/manifest.json`
- Create: `/home/agdis/pm-os-gcp/extensions/bodycam-browser/background.js`
- Create: `/home/agdis/pm-os-gcp/extensions/bodycam-browser/content.js`

- [ ] **Step 1: Write manifest.json (Manifest V3)**

```json
{
  "manifest_version": 3,
  "name": "BodyCam Browser",
  "version": "1.0.0",
  "description": "PM-OS BodyCam — captures all browser activity for agent observability",
  "permissions": [
    "webRequest",
    "tabs",
    "activeTab",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

- [ ] **Step 2: Write background.js — captures all HTTP requests**

```javascript
// background.js — BodyCam Browser Extension
// Captures all web requests and forwards to BodyCam endpoint

const BODYCAM_ENDPOINT = "http://localhost:8082/bodycam/browser";
const BUFFER = [];
const FLUSH_INTERVAL_MS = 5000;

// Capture all web requests
chrome.webRequest.onCompleted.addListener(
  (details) => {
    const event = {
      timestamp: new Date().toISOString(),
      layer: "browser",
      type: "web_request",
      data: {
        request_id: details.requestId,
        url: details.url,
        method: details.method,
        status_code: details.statusCode,
        type: details.type, // main_frame, script, xhr, image, etc
        initiator: details.initiator || "",
        tab_id: details.tabId,
        from_cache: details.fromCache,
        ip: details.ip || "",
        response_headers: details.responseHeaders
          ? Object.fromEntries(details.responseHeaders.map(h => [h.name, h.value]))
          : {},
      },
    };
    BUFFER.push(event);
  },
  { urls: ["<all_urls>"] },
  ["responseHeaders"]
);

// Capture tab changes (which page is active)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  BUFFER.push({
    timestamp: new Date().toISOString(),
    layer: "browser",
    type: "tab_activated",
    data: {
      tab_id: tab.id,
      url: tab.url,
      title: tab.title,
    },
  });
});

// Capture navigation
chrome.webNavigation?.onCompleted.addListener((details) => {
  BUFFER.push({
    timestamp: new Date().toISOString(),
    layer: "browser",
    type: "navigation",
    data: {
      tab_id: details.tabId,
      url: details.url,
      frame_id: details.frameId,
    },
  });
});

// Flush buffer periodically
setInterval(async () => {
  if (BUFFER.length === 0) return;
  const batch = BUFFER.splice(0, BUFFER.length);
  try {
    await fetch(BODYCAM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: batch }),
    });
  } catch (e) {
    // Endpoint down — re-queue events
    BUFFER.unshift(...batch);
    if (BUFFER.length > 10000) BUFFER.length = 10000; // cap memory
  }
}, FLUSH_INTERVAL_MS);
```

- [ ] **Step 3: Write content.js — captures DOM interactions (clicks, form inputs)**

```javascript
// content.js — BodyCam Browser Extension
// Captures user interactions on every page

function sendEvent(type, data) {
  chrome.runtime?.sendMessage({
    timestamp: new Date().toISOString(),
    layer: "browser",
    type: type,
    data: {
      url: window.location.href,
      title: document.title,
      ...data,
    },
  });
}

// Capture clicks
document.addEventListener("click", (e) => {
  const el = e.target;
  sendEvent("click", {
    tag: el.tagName,
    text: (el.textContent || "").slice(0, 200),
    id: el.id,
    class: el.className,
    href: el.href || "",
    x: e.clientX,
    y: e.clientY,
  });
}, true);

// Capture form submissions
document.addEventListener("submit", (e) => {
  const form = e.target;
  sendEvent("form_submit", {
    action: form.action,
    method: form.method,
    id: form.id,
  });
}, true);

// Capture input changes (debounced, no passwords)
let inputTimeout;
document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.type === "password") return; // never capture passwords
  clearTimeout(inputTimeout);
  inputTimeout = setTimeout(() => {
    sendEvent("input_change", {
      tag: el.tagName,
      type: el.type,
      name: el.name,
      id: el.id,
      value_length: (el.value || "").length, // length only, not content for privacy
    });
  }, 500);
}, true);

// Forward content script events to background
chrome.runtime?.onMessage.addListener((msg) => {
  // background.js picks these up and adds to BUFFER
});
```

- [ ] **Step 4: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add extensions/bodycam-browser/
git commit -m "feat(bodycam): Chrome extension — captures web requests, navigation, clicks, form interactions"
```

### Task 5.2: Browser Event Receiver Endpoint (in android-agent or pm-api)

**Files:**
- Modify: `/home/agdis/pm-os-gcp/cmd/pm-android-agent/main.go`

- [ ] **Step 1: Add /bodycam/browser endpoint**

```go
// In main(), add route:
http.HandleFunc("/bodycam/browser", func(w http.ResponseWriter, r *http.Request) {
    var payload struct {
        Events []json.RawMessage `json:"events"`
    }
    if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
        http.Error(w, err.Error(), 400)
        return
    }

    sink := bodycam.NewCloudLoggingSink()
    for _, raw := range payload.Events {
        var ev bodycam.Event
        json.Unmarshal(raw, &ev)
        ev.AgentID = "browser-agent"
        ev.DeviceID = "agdis-chrome"
        sink(ev)
    }

    log.Info().Int("events", len(payload.Events)).Msg("browser bodycam batch received")
    w.WriteHeader(204)
})
```

- [ ] **Step 2: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add cmd/pm-android-agent/
git commit -m "feat(bodycam): browser event receiver endpoint in android-agent"
```

---

## Sub 6: Infraestrutura GCP (BigQuery + Log Sinks + GCS Bucket)

> Configurar a infraestrutura que recebe e armazena todos os dados.

### Task 6.1: BigQuery Dataset + Table Schema

**Files:**
- Create: `/home/agdis/pm-os-gcp/scripts/bodycam/setup-bigquery.sh`

- [ ] **Step 1: Write BigQuery setup script**

```bash
#!/bin/bash
# setup-bigquery.sh — Cria dataset e tabela no BigQuery pra BodyCam
set -e

PROJECT="circular-transport-pr8vp"
DATASET="bodycam"
TABLE="events"

echo "=== Creating BigQuery dataset ==="
bq mk --dataset --location=us-central1 \
    --description="BodyCam observability data — all agent activity" \
    "$PROJECT:$DATASET" 2>/dev/null || echo "Dataset already exists"

echo "=== Creating events table ==="
bq mk --table "$PROJECT:$DATASET.$TABLE" \
    trace_id:STRING,\
    agent_id:STRING,\
    device_id:STRING,\
    timestamp:TIMESTAMP,\
    layer:STRING,\
    type:STRING,\
    data:JSON,\
    severity:STRING,\
    method:STRING,\
    path:STRING,\
    status:INTEGER,\
    duration_ms:INTEGER,\
    request_body:STRING,\
    response_body:STRING \
    2>/dev/null || echo "Table already exists"

echo "=== Creating Cloud Logging sink → BigQuery ==="
gcloud logging sinks create bodycam-to-bigquery \
    "bigquery.googleapis.com/projects/$PROJECT/datasets/$DATASET" \
    --log-filter='jsonPayload.message=~"^bodycam:"' \
    --project="$PROJECT" \
    2>/dev/null || echo "Sink already exists"

# Grant BigQuery write access to the logging service account
SINK_SA=$(gcloud logging sinks describe bodycam-to-bigquery --project="$PROJECT" --format='value(writerIdentity)')
bq add-iam-policy-binding --member="$SINK_SA" --role="roles/bigquery.dataEditor" "$PROJECT:$DATASET"

echo "=== Creating GCS bucket for media ==="
gcloud storage buckets create "gs://bodycam-media-$PROJECT" \
    --location=us-central1 \
    --uniform-bucket-level-access \
    --lifecycle-file=/dev/stdin << 'LIFECYCLE'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }
  ]
}
LIFECYCLE

echo "=== Done ==="
echo "BigQuery: $PROJECT.$DATASET.$TABLE"
echo "GCS: gs://bodycam-media-$PROJECT"
echo "Log Sink: bodycam-to-bigquery (filters messages starting with 'bodycam:')"
```

- [ ] **Step 2: Run setup on Cloud Shell or local gcloud**

Run: `bash /home/agdis/pm-os-gcp/scripts/bodycam/setup-bigquery.sh`

- [ ] **Step 3: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add scripts/bodycam/setup-bigquery.sh
git commit -m "feat(bodycam): BigQuery dataset + Cloud Logging sink + GCS bucket setup"
```

### Task 6.2: Metabase Dashboard Queries

**Files:**
- Create: `/home/agdis/pm-os-gcp/scripts/bodycam/metabase-queries.sql`

- [ ] **Step 1: Write the key queries for Metabase dashboards**

```sql
-- metabase-queries.sql
-- Queries prontas pra criar dashboards de BodyCam no Metabase

-- 1. Timeline completa de uma task (todas as camadas)
-- Parametro: {{trace_id}}
SELECT
  timestamp,
  layer,
  type,
  agent_id,
  device_id,
  JSON_VALUE(data, '$.url') as url,
  JSON_VALUE(data, '$.method') as method,
  JSON_VALUE(data, '$.status_code') as status_code,
  JSON_VALUE(data, '$.screenshot_url') as screenshot,
  JSON_VALUE(data, '$.transcript') as audio_transcript,
  CAST(JSON_VALUE(data, '$.duration_ms') AS INT64) as duration_ms,
  data
FROM `circular-transport-pr8vp.bodycam.events`
WHERE trace_id = {{trace_id}}
ORDER BY timestamp ASC;

-- 2. Volume de eventos por camada (últimas 24h)
SELECT
  layer,
  type,
  COUNT(*) as event_count,
  TIMESTAMP_TRUNC(timestamp, HOUR) as hour
FROM `circular-transport-pr8vp.bodycam.events`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY layer, type, hour
ORDER BY hour DESC, event_count DESC;

-- 3. Tráfego de rede do celular — top domains
SELECT
  NET.HOST(JSON_VALUE(data, '$.request.url')) as domain,
  COUNT(*) as requests,
  AVG(CAST(JSON_VALUE(data, '$.duration_ms') AS INT64)) as avg_latency_ms,
  COUNTIF(CAST(JSON_VALUE(data, '$.response.status_code') AS INT64) >= 400) as errors
FROM `circular-transport-pr8vp.bodycam.events`
WHERE layer = 'network' AND type = 'http_exchange'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY domain
ORDER BY requests DESC
LIMIT 50;

-- 4. Ações do agente Android — replay visual
SELECT
  timestamp,
  type,
  JSON_VALUE(data, '$.action') as action,
  JSON_VALUE(data, '$.screenshot_url') as screenshot,
  JSON_VALUE(data, '$.ui_tree_nodes') as ui_elements,
  JSON_VALUE(data, '$.phone_state.current_app') as app,
  CAST(JSON_VALUE(data, '$.duration_ms') AS INT64) as duration_ms
FROM `circular-transport-pr8vp.bodycam.events`
WHERE layer = 'visual' AND agent_id = {{agent_id}}
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY timestamp ASC;

-- 5. PM-OS server traces — pipeline execution
SELECT
  timestamp,
  JSON_VALUE(data, '$.task.id') as task_id,
  JSON_VALUE(data, '$.task.type') as task_type,
  JSON_VALUE(data, '$.task.agent') as agent,
  JSON_VALUE(data, '$.llm.provider') as llm_model,
  CAST(JSON_VALUE(data, '$.llm.cost_usd') AS FLOAT64) as cost_usd,
  CAST(JSON_VALUE(data, '$.llm.tokens_out') AS INT64) as tokens_out,
  CAST(JSON_VALUE(data, '$.llm.duration_ms') AS INT64) as llm_latency_ms
FROM `circular-transport-pr8vp.bodycam.events`
WHERE layer = 'server'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;

-- 6. Browser activity — páginas visitadas + interações
SELECT
  timestamp,
  type,
  JSON_VALUE(data, '$.url') as url,
  JSON_VALUE(data, '$.title') as page_title,
  JSON_VALUE(data, '$.tag') as element_tag,
  JSON_VALUE(data, '$.text') as element_text
FROM `circular-transport-pr8vp.bodycam.events`
WHERE layer = 'browser'
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY timestamp DESC;

-- 7. Custo total LLM por hora (últimas 48h)
SELECT
  TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
  SUM(CAST(JSON_VALUE(data, '$.llm.cost_usd') AS FLOAT64)) as total_cost_usd,
  SUM(CAST(JSON_VALUE(data, '$.llm.tokens_out') AS INT64)) as total_tokens_out,
  COUNT(*) as llm_calls
FROM `circular-transport-pr8vp.bodycam.events`
WHERE layer = 'server' AND JSON_VALUE(data, '$.llm.cost_usd') IS NOT NULL
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
GROUP BY hour
ORDER BY hour DESC;
```

- [ ] **Step 2: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add scripts/bodycam/metabase-queries.sql
git commit -m "feat(bodycam): Metabase dashboard queries — 7 views covering all bodycam layers"
```

---

## Sub 7: Setup do Celular (DroidRun Portal + PCAPdroid)

> Configuração manual do Moto G04s — passos para o Kemuel/Dis executar.

### Task 7.1: Checklist de Setup do Celular

- [ ] **Step 1: Instalar DroidRun Portal**

Abrir Chrome no Moto G04s → navegar para:
`https://github.com/droidrun/droidrun-portal/releases/download/v0.6.1/droidrun-portal-v0.6.1.apk`
Baixar e instalar. Permitir fonte desconhecida.

- [ ] **Step 2: Ativar Accessibility Service**

Configurações → Acessibilidade → DroidRun Portal → Ativar

- [ ] **Step 3: Instalar PCAPdroid**

Play Store → buscar "PCAPdroid" → instalar (versão gratuita serve)

- [ ] **Step 4: Configurar PCAPdroid como proxy para mitmproxy**

PCAPdroid → Settings → SOCKS5 proxy:
- Host: IP Tailscale da máquina agdis (ex: `100.x.x.x`)
- Port: `8888`

- [ ] **Step 5: Instalar certificado CA do mitmproxy no celular**

```bash
# Na máquina agdis, copiar cert pro celular:
scp -P 8022 ~/.mitmproxy/mitmproxy-ca-cert.pem 100.97.136.4:~/
# No celular: Configurações → Segurança → Instalar certificado → selecionar o .pem
```

- [ ] **Step 6: Patch de APKs com certificate pinning (Instagram, WhatsApp, etc)**

```bash
# Na máquina agdis:
bash /home/agdis/pm-os-gcp/scripts/bodycam/patch-apk.sh com.instagram.android
bash /home/agdis/pm-os-gcp/scripts/bodycam/patch-apk.sh com.whatsapp
# Instalar APKs patched no celular
```

- [ ] **Step 7: Verificar conectividade**

```bash
# Na máquina agdis:
curl http://100.97.136.4:8080/ping
# Esperado: {"status":"success","result":"pong"}
```

---

## Dockerfile para pm-android-agent

### Task 8.1: Containerizar o Android Agent

**Files:**
- Create: `/home/agdis/pm-os-gcp/Dockerfile.android-agent`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o pm-android-agent ./cmd/pm-android-agent/

FROM alpine:3.21
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/pm-android-agent .
EXPOSE 8082
ENV PORT=8082
CMD ["./pm-android-agent"]
```

- [ ] **Step 2: Add to cloudbuild.yaml**

Add new build step alongside pm-api and pm-worker:

```yaml
  # Build pm-android-agent
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'Dockerfile.android-agent', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/pm-os/pm-android-agent:$SHORT_SHA', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/pm-os/pm-android-agent:$SHORT_SHA']

  # Deploy pm-android-agent
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pm-android-agent'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/pm-os/pm-android-agent:$SHORT_SHA'
      - '--region=us-central1'
      - '--memory=512Mi'
      - '--cpu=1'
      - '--min-instances=1'
      - '--max-instances=2'
      - '--set-env-vars=PORTAL_HOST=100.97.136.4:8080'
      - '--set-env-vars=GCP_PROJECT_ID=$PROJECT_ID'
```

**Nota:** O PORTAL_HOST via Tailscale requer que o Cloud Run tenha acesso ao Tailscale. Alternativa: rodar o android-agent na **máquina agdis** em vez de Cloud Run, já que agdis já está no Tailscale.

- [ ] **Step 3: Commit**

```bash
cd /home/agdis/pm-os-gcp
git add Dockerfile.android-agent cloudbuild.yaml
git commit -m "feat(android-agent): Dockerfile + Cloud Build deploy config"
```

---

## Ordem de Execução Recomendada

```
Wave 1 (paralelo — sem conflitos de arquivo):
  ├─ Task 1.1 + 1.2: Portal Client (pkg/android/)
  ├─ Task 2.1 + 2.2: BodyCam Logger + Sinks (pkg/bodycam/)
  ├─ Task 4.1: OTel Setup (pkg/telemetry/)
  └─ Task 5.1: Chrome Extension (extensions/)

Wave 2 (paralelo — depende de Wave 1):
  ├─ Task 1.3: Android Agent Service (cmd/pm-android-agent/ — depende de 1.1+1.2)
  ├─ Task 2.3 + 2.4: GCS Upload + Audio (pkg/bodycam/ — depende de 2.1)
  ├─ Task 4.2: HTTP Middleware (pkg/telemetry/ — depende de 4.1)
  ├─ Task 3.1: mitmproxy setup (scripts/ — independente)
  └─ Task 6.1: BigQuery infra (scripts/ — independente)

Wave 3 (paralelo — depende de Wave 2):
  ├─ Task 4.3: Instrument pm-api (cmd/pm-api/ — depende de 4.2)
  ├─ Task 4.4: Instrument pm-worker (cmd/pm-worker/ — depende de 4.1)
  ├─ Task 4.5: Instrument Pub/Sub (pkg/orchestration/ — depende de 4.1)
  ├─ Task 3.2: Traffic Forwarder (pkg/bodycam/ — depende de 3.1)
  └─ Task 5.2: Browser Event Receiver (cmd/pm-android-agent/ — depende de 1.3)

Wave 4 (sequencial):
  ├─ Task 3.3: APK Patching script
  ├─ Task 6.2: Metabase queries
  ├─ Task 7.1: Setup celular (manual)
  └─ Task 8.1: Dockerfile + deploy

Devs necessários: 5 (Wave 1-2), 5 (Wave 3), 1 (Wave 4)
Tempo estimado com waves: ~4-6 horas
```

---

## Decisões Arquiteturais

1. **android-agent na máquina agdis, não no Cloud Run** — porque precisa de Tailscale pra acessar o celular. Cloud Run não tem Tailscale. Roda como systemd service na agdis.

2. **Cloud Logging como transport universal** — todos os serviços já rodam em Cloud Run que captura stdout automaticamente. O log sink pro BigQuery é configuração GCP, zero código extra.

3. **mitmproxy na agdis, não no GCP** — mesma razão do Tailscale. O celular aponta o proxy pra agdis via Tailscale IP.

4. **Chrome Extension no navegador da agdis** — a máquina é recurso do agente, extensão captura toda atividade web.

5. **Não usamos DroidRun Python SDK** — o PM-OS é Go, seria inconsistente. O Portal Client Go que escrevemos faz a mesma coisa via HTTP direto.

6. **Privacy: content.js não captura conteúdo de password fields** — segurança básica.

7. **JSONL como formato intermediário do mitmproxy** — o addon Python escreve JSONL, o Go forwarder lê e manda pro Cloud Logging. Desacoplado.

8. **Deploy otimizado com Docker layer cache** — Artifact Registry mantém cache de layers. Como go.mod muda pouco, `go mod download` é cacheado e rebuild leva ~2-3 min em vez de 8-10 min. Cloud Run source deploy (conectar repo) é outra opção mas Cloud Build com cache dá mais controle.
