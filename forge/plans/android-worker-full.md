# Android Worker + PM-OS Integration — Implementation Plan

**Goal:** Implementar o worker Android completo que conecta o PM-OS ao celular via DroidRun Portal, com integração do Forge como motor de code generation delegado.

---

### Task 1.1: Portal Client Types

**Files:**
- Create: `pkg/android/types.go`

Criar os types base para comunicação com DroidRun Portal:
- PortalResponse struct {Status string; Result interface{}; Error string}
- PhoneState struct {CurrentApp string; FocusedElement string; KeyboardVisible bool}
- A11yNode struct {Index int; Text string; Class string; Bounds string; Clickable bool; Scrollable bool; Editable bool}
- Key code constants (Enter=66, Back=4, Home=3, Backspace=67, Tab=61, Escape=111)

Run: `go build ./pkg/android/`

### Task 1.2: Portal Client HTTP Methods

**Files:**
- Create: `pkg/android/portal_client.go`
- Create: `pkg/android/portal_client_test.go`

HTTP client para DroidRun Portal API (HTTP :8080):
- NewPortalClient(baseURL, authToken string) *PortalClient
- Ping() error — GET /ping
- GetA11yTree() ([]A11yNode, error) — GET /a11y_tree
- GetPhoneState() (*PhoneState, error) — GET /phone_state
- GetFullState() (*PortalResponse, error) — GET /state_full?filter=false
- InputText(text string) error — POST /keyboard/input (base64 encoded)
- ClearText() error — POST /keyboard/clear
- PressKey(keyCode int) error — POST /keyboard/key
- GetInstalledApps() ([]string, error) — GET /packages
Internal: get(path) and post(path, params) helpers with auth header and 10s timeout.
Tests com httptest.NewServer mockando cada endpoint.

Run: `go test ./pkg/android/ -v`

### Task 1.3: Android Agent Service

**Files:**
- Create: `pkg/android/agent.go`
- Create: `pkg/android/agent_test.go`

Agent struct que recebe tasks do PM-OS e executa no Portal:
- AgentTask struct {TaskID, Action, Target, Text, RunID string}
- AgentResult struct {TaskID, Status string; Data interface{}; Error string; Duration int64; Timestamp time.Time}
- NewAgent(portal *PortalClient) *Agent
- Execute(task AgentTask) (*AgentResult, error)
Actions: get_screen_state, get_phone_state, get_tree, input_text, press_key, get_apps, open_app
Tests com httptest mock do Portal.

Run: `go test ./pkg/android/ -run TestAgent -v`

### Task 1.4: Agent HTTP Entry Point

**Files:**
- Create: `cmd/pm-android-agent/main.go`

Servidor HTTP standalone que roda na máquina agdis:
- Port: 8082 (env PORT)
- GET /health — pinga o Portal, retorna status
- POST /execute — recebe AgentTask JSON, executa, retorna AgentResult
- Env: PORTAL_HOST (ex: 100.97.136.4:8080), PORTAL_TOKEN
- Loga com zerolog (import do pkg/logger existente)

Run: `go build ./cmd/pm-android-agent/`

### Task 2.1: BodyCam Event Types

**Files:**
- Create: `pkg/bodycam/types.go`

Event types para o sistema de observabilidade:
- Layer constants: LayerVisual, LayerNetwork, LayerServer, LayerAudio, LayerBrowser
- Event struct {TraceID, AgentID, DeviceID string; Timestamp time.Time; Layer, Type string; Data map[string]interface{}}
- BigQuery tags nos campos

Run: `go build ./pkg/bodycam/`

### Task 2.2: BodyCam Logger

**Files:**
- Create: `pkg/bodycam/logger.go`
- Create: `pkg/bodycam/logger_test.go`

Logger com pluggable sinks:
- SinkFunc type = func(Event) error
- NewLogger(agentID, deviceID string, sink SinkFunc) *Logger
- Logger.SetTraceID(id string)
- Logger.Log(layer, eventType string, data map[string]interface{}) error
Thread-safe com sync.Mutex. Testes com sink mock.

Run: `go test ./pkg/bodycam/ -v`

### Task 2.3: BodyCam Cloud Logging Sink

**Files:**
- Create: `pkg/bodycam/sink_logging.go`
- Create: `pkg/bodycam/sink_logging_test.go`

Sink que escreve JSON estruturado no stdout (Cloud Run captura automaticamente):
- formatLogEntry(ev Event) []byte — formata como Cloud Logging JSON
- NewCloudLoggingSink() SinkFunc
Output: {severity, message:"bodycam:layer:type", timestamp, labels:{layer,type,agent_id,device_id}, trace_id, bodycam:{data}}

Run: `go test ./pkg/bodycam/ -run TestCloudLogging -v`

### Task 3.1: OpenTelemetry Setup Package

**Files:**
- Create: `pkg/telemetry/otel.go`
- Create: `pkg/telemetry/otel_test.go`

OTel initialization com Google Cloud Trace exporter:
- InitTracer(ctx, serviceName, gcpProjectID string, localDev bool) (shutdown func, error)
- Tracer(name string) trace.Tracer — returns named tracer from global provider
- noopExporter para testes
Deps: go.opentelemetry.io/otel, otel/sdk/trace, GoogleCloudPlatform/opentelemetry-operations-go/exporter/trace

Run: `go test ./pkg/telemetry/ -v`

### Task 3.2: BodyCam HTTP Middleware

**Files:**
- Create: `pkg/telemetry/middleware.go`
- Create: `pkg/telemetry/middleware_test.go`

Middleware que captura request/response com OTel spans:
- BodyCamMiddleware(next http.Handler, logFn LogFunc) http.Handler
- responseRecorder wraps ResponseWriter to capture status + body
- Captura: method, path, status, duration_ms, request_body (4KB max), response_body (4KB max)
- Cria span com http.method, http.path, http.status_code, http.duration_ms
- LogFunc = nil → stdout JSON (Cloud Logging)
Tests com httptest.

Run: `go test ./pkg/telemetry/ -run TestMiddleware -v`

### Task 4.1: Systemd Service + Deploy Script

**Files:**
- Create: `scripts/bodycam/android-agent.service`
- Create: `scripts/bodycam/deploy-android-agent.sh`

Systemd service para rodar pm-android-agent na máquina agdis:
- ExecStart=/home/agdis/pm-os-gcp/pm-android-agent
- Environment: PORTAL_HOST=100.97.136.4:8080, PORT=8082
- Restart=always, User=agdis
- Deploy script: go build → copy binary → systemctl restart

Run: `cat scripts/bodycam/android-agent.service`

### Task 4.2: PM-OS Forge Integration Endpoint

**Files:**
- Create: `scripts/bodycam/forge-integration.sh`

Script que registra o forge como capability no PM-OS:
- Testa conectividade com pm-api
- Submete task de teste
- Verifica resultado
- Configura variáveis de ambiente pra forge.py

Run: `bash scripts/bodycam/forge-integration.sh`

### Task 5.1: Dockerfile Worker Full

**Files:**
- Create: `Dockerfile.worker-full`

Worker com todos os recursos (browser, gcloud, Go):
- Base: Dockerfile.worker existente
- + npx playwright install --with-deps chromium
- + gcloud CLI
- + Go 1.25
- Pra tasks que precisam de browser, deploy, build

Run: `docker build -f Dockerfile.worker-full -t pm-worker-full .`
