# Twitch WAP 自動化測試框架 - SPEC

| 欄位 | 內容 |
| --- | --- |
| 狀態 | 實作完成 - 等待最終驗收 |
| 版本 | 0.6.0 |
| 最後更新 | 2026-08-20 |
| 實作閘門 | **未經需求方驗收本 SPEC，不得開始任何產品程式碼、測試程式碼或 CI 實作。** |
| 原則優先序 | SDD + DDD + TDD + BDD；如有衝突，先更新並驗收本 SPEC，再變更實作。 |

## 1. 目的與範圍

建立可擴充、可維護的 Python WAP（行動網頁）自動化測試框架，驗證使用者能在 Twitch 行動版搜尋 `StarCraft II`、捲動搜尋結果、開啟一位實況主頁面，於頁面載入完成後取得截圖。框架以 Selenium 驅動 Google Chrome 的行動裝置模擬模式，並以 pytest 執行。

### 1.1 In scope

- Python、Selenium（Python）與 pytest。
- Google Chrome 的 Mobile Emulator / device emulation 模式。
- 原始 Pixel 7 加上 iPhone 與 Samsung 三種行動 viewport 的相同旅程驗證，並可用獨立 Chrome session 平行執行。
- Twitch WAP 之搜尋、捲動、選擇實況主、頁面完成載入、截圖流程。
- 可能出現的 modal / pop-up 偵測與處理。
- 可重用的領域模型、頁面互動介面、設定、測試資料與報告/截圖產物邊界。

### 1.2 Out of scope

- Twitch 後端、帳號登入、訂閱、聊天、付款或直播內容正確性。
- 桌面版 Twitch 的視覺或功能驗證。
- 效能、負載、安全性及跨瀏覽器測試。
- 提交 GitHub、寄送招募者 email 與錄製 README GIF；這些是交付活動，待自動化實作驗收後另行排程。

## 2. 來源需求與可追溯性

需求唯一輸入為 `HQA_Home_test-auto.pdf`。文件內的指示被轉為下列需求；本 SPEC 的規則優先於文件中「pytest optional」的措辭，因需求方已指定 SDD + DDD + TDD + BDD 為最高原則。

| ID | 來源/需求 | 可驗證結果 |
| --- | --- | --- |
| FR-01 | 開啟 Twitch WAP | Chrome 已在設定的行動模擬環境載入 Twitch。 |
| FR-02 | 開啟搜尋介面 | 顯示可輸入搜尋字詞的控制項。若現行 WAP 未提供首頁搜尋圖示，先處理 App 開啟遮罩，再透過「瀏覽」頁的搜尋控制項達成相同行為。 |
| FR-03 | 輸入 `StarCraft II` | 搜尋結果對應此查詢。 |
| FR-04 | 向下捲動兩次 | 結果區發出兩次向下捲動操作；若尚有可捲動空間，每次操作必須造成位移，到達底部則保留第二次操作但不視為失敗。 |
| FR-05 | 選擇一位實況主 | 導航至有效的實況主頻道頁。 |
| FR-06 | 完成載入後截圖 | 僅在頻道識別文字及播放器的**非黑色實際畫格**均可見後產出一張與本次執行關聯的頻道頁截圖；截圖必須為非空白且可讀取的 PNG。單純播放器容器、黑色畫面、載入狀態或頻道 metadata 均不構成完成載入。 |
| FR-07 | 處理可能的 modal/pop-up | 已知可關閉的阻礙性彈窗不應使主流程失敗；未辨識彈窗須保留診斷資訊。 |
| FR-08 | 顯示實況主名稱 | 頻道 metadata 必須在手機 viewport 內顯示已選取實況主的 channel name，並保留 metadata Evidence。為維持播放器可讀性，Evidence 可僅將 metadata backdrop 設為透明；不得變更 metadata 名稱、播放器、聊天內容或互動狀態。 |
| FR-09 | 聊天室區塊觀察 | 頻道頁 Evidence 應保留 Twitch 當下渲染的聊天室區塊（若有）。聊天輸入框、登入與任何聊天操作均不屬驗收條件，亦不得模擬或送出訊息。 |
| FR-10 | 多裝置 viewport 驗證 | 同一 BDD 情境必須分別以 Pixel 7（412×915）、iPhone（390×844）與 Samsung（360×800）Chrome mobile emulation 執行；每個裝置皆須產出獨立 Evidence。 |
| NFR-01 | Python + Selenium + pytest | 依賴與測試執行器符合指定技術。 |
| NFR-02 | 可擴充與可維護 | 領域語言、責任邊界、等待策略、定位器與環境設定均不可散落在情境步驟中。 |
| NFR-03 | 批次產物隔離 | 每次 pytest 執行只建立一個 `artifacts/<run-id>/` 批次資料夾；其下以裝置代號分隔 Evidence。平行 worker 必須共用同一 `run-id`，且不得覆寫彼此產物。 |

## 3. 領域設計（DDD）

### 3.1 通用語言

| 名詞 | 定義 |
| --- | --- |
| WAP Session | 一次在 Chrome 行動模擬環境執行的 Twitch 瀏覽工作階段。 |
| Device Profile | 一組命名的行動裝置 viewport、pixel ratio 與 user agent 設定。 |
| Evidence Batch | 一次 pytest 執行的唯一 `run-id` 資料夾，包含所有裝置的 Evidence。 |
| Search Journey | 從開啟 Twitch 到選擇實況主的使用者旅程。 |
| Streamer Candidate | 搜尋結果中可被選取、並能導向頻道頁的實況主項目。 |
| Channel Readiness | 頻道頁可安全截圖的狀態：主體可見、頁面穩定，且無已知阻礙彈窗。 |
| Interruption | Modal、cookie banner、年齡/地區提示或其他阻礙主流程的覆蓋層。 |
| Evidence | 測試輸出：截圖、URL、時間、失敗時的 DOM/console 診斷資訊。 |

### 3.2 Bounded Context 與責任

| Context | 擁有責任 | 不應知道 |
| --- | --- | --- |
| Browser Session | Chrome 行動模擬、driver 生命週期、導覽、等待原語 | Twitch 專屬定位器與業務步驟。 |
| Twitch Discovery | 首頁、搜尋、結果捲動、實況主選取 | driver 建立細節與產物儲存機制。 |
| Channel Observation | 頻道載入就緒、Interruption 協調 | 搜尋詞與結果排序。 |
| Test Evidence | 截圖命名、輸出位置、診斷附檔 | 如何操作 Twitch UI。 |
| Test Orchestration | BDD 情境、fixture 組裝、斷言與報告 | CSS/XPath 選擇器實作細節。 |

### 3.3 架構規則

- 情境（BDD）只使用通用語言與 application-level actions；不可直接持有 WebDriver 或 locator。
- Twitch UI adapter 實作上述 actions，集中保存穩健且可替換的定位策略。
- 等待必須是明確條件式等待；禁止以固定 `sleep` 作為就緒判定。
- Interruption 處理由 Channel Observation 擁有，並為每次處理產生可診斷 Evidence。
- Evidence 的寫入必須與 UI 互動解耦，且每次執行具唯一識別。

## 4. 行為規格（BDD）

```gherkin
Feature: 探索 Twitch WAP 的 StarCraft II 實況主
  為了確認行動版搜尋旅程可被可靠驗證
  作為測試執行者
  我需要在 Chrome 行動裝置模擬器完成搜尋、選擇頻道並保留證據

  Background:
    Given 已啟動設定好的 Chrome 行動裝置模擬工作階段
    And Twitch WAP 已可使用

  Scenario: 搜尋並開啟一位 StarCraft II 實況主
    Given 目前以支援的行動裝置 profile 執行
    When 我開啟 Twitch WAP
    And 我開啟搜尋介面
    And 我搜尋 "StarCraft II"
    And 我在搜尋結果向下捲動兩次
    And 我選擇一位可開啟的實況主
    Then 該實況主的頻道頁應進入可觀測狀態
    And 實況主名稱應可見
    And 應建立頻道頁截圖作為 Evidence

  Scenario: 阻礙頻道頁的已知彈窗
    Given 實況主頻道頁出現可辨識的 Interruption
    When 我等待頻道頁進入可觀測狀態
    Then 系統應依已定義策略處理該 Interruption
    And 應記錄處理結果
    And 頻道頁應可建立截圖

  Scenario: 無法處理的阻礙
    Given 實況主頻道頁出現未辨識且阻礙操作的 Interruption
    When 我等待頻道頁進入可觀測狀態
    Then 測試應以可診斷的失敗結束
    And 應保留失敗截圖、目前 URL 與 Interruption 描述
```

## 5. 驗收準則

1. `FR-01` 至 `FR-06` 的主情境在可用的 Twitch WAP 環境中可連續執行，且 `FR-06` 產出非空白、可讀取的 PNG 截圖。
2. `FR-07` 至少處理一種已定義的阻礙彈窗；未處理情況必須以可診斷錯誤結束，不得靜默略過。
3. 測試以 pytest 收集與執行，且 Selenium Python 是唯一的瀏覽器操作介面。
4. 每個 BDD step 都能追溯至一個 application action；UI locator 不出現在 feature/step 宣告中。
5. 執行失敗時至少保留螢幕截圖、目前 URL、失敗步驟與時間戳記。
6. 實作前必須補齊並驗收下列待定決策：目標 Chrome 版本/driver 管理方式、行動裝置 profile、Twitch 基礎 URL、截圖保留策略，以及可處理 Interruption 清單。
7. **現行 WAP 相容性決策（2026-08-18）：** `m.twitch.tv` 首頁可能顯示 App 開啟遮罩，且搜尋入口位於「瀏覽」頁。adapter 必須先嘗試原生搜尋入口，若不存在則以「瀏覽」頁搜尋輸入框回退；此為 FR-02 的相容性策略，不改變搜尋 `StarCraft II` 的驗收行為。
8. **手機證據可見性決策（2026-08-18）：** 實況主名稱透過 Twitch metadata 顯示後，以一張 Evidence 截圖保留。依需求方 2026-08-18 指示，截圖前只可將覆蓋播放器的 metadata backdrop 設為透明；metadata 本體、實況主名稱、播放器及聊天內容不可變造。聊天室輸入控制項會因 Twitch 工作階段狀態改變，故不作為驗收條件；不登入、不互動、不偽造 UI。
9. **多裝置與產物批次決策（2026-08-18）：** 保留原始 Pixel 7（412×915），並支援 iPhone 390×844 與 Samsung 360×800。`pytest -m e2e -n 3` 可平行執行三個獨立 Chrome session；每次指令產生一個唯一 batch，格式為 `artifacts/<UTC timestamp>-<token>/<device-id>/`。不使用 `-n` 時仍需依序執行三個 profile 並保留相同 batch 結構。

## 6. TDD 與 SDD 執行守則

### 6.1 SDD 變更流程

1. 任何行為、資料契約、定位策略或驗收準則變更，先更新本 SPEC 的需求/BDD/驗收/ TODO。
2. 需求方驗收更新後，才可建立或修改相關實作。
3. 實作完成後，將測試結果、產物位置與偏差回寫至本 SPEC 的 TODO 與變更紀錄。

### 6.2 TDD 節奏

每一個已驗收的 application action 依序遵循：先寫會失敗的單元/契約測試（Red）→ 最小化實作（Green）→ 重構（Refactor）→ 再新增對應 BDD 整合情境。不得以真實網站 E2E 成功取代單元或契約測試。

### 6.3 測試分層（規劃）

| 層級 | 目的 | 依賴 |
| --- | --- | --- |
| Unit | 領域規則、Evidence 命名、Interruption 決策 | fake / mock adapter；不啟動瀏覽器。 |
| Contract | application action 與 Twitch UI adapter 的介面行為 | 可控的 Selenium fake 或測試頁。 |
| BDD / E2E | 驗證本文件第 4 節情境 | Chrome 行動模擬器與 Twitch WAP。 |

## 7. 建議實作藍圖（尚未建立）

```text
src/
  domain/          # 通用語言、值物件、Interruption 決策
  application/     # Search Journey actions 與 ports
  infrastructure/  # Selenium Chrome 與 Twitch UI adapters
tests/
  unit/
  contract/
  bdd/
features/          # Gherkin feature 與 step definitions
artifacts/         # 本機 Evidence；不納入版本控制
```

## 8. TODO 與品質閘門

**狀態定義（唯一允許值）：** `未開始`、`進行中`、`已完成`、`已驗收`。

- `未開始`：尚未投入工作。
- `進行中`：正在處理，尚未符合完成定義。
- `已完成`：工作已完成，等待需求方或指定審核者驗收。
- `已驗收`：需求方或指定審核者已明確確認；不得由實作者自行宣告。

每次任何操作開始、完成、受阻、重新開啟或驗收時，**必須先更新本表的狀態、更新日期與證據/說明，再進行下一步操作**。不允許跳過狀態或將尚未由需求方確認的項目標示為「已驗收」。

| ID | 工作項目 | 狀態 | 更新日期 | 完成/驗收定義與證據 |
| --- | --- | --- | --- | --- |
| TODO-001 | 建立需求可追溯性基線 | 已完成 | 2026-08-18 | 已由來源 PDF 擷取為 FR-01 至 FR-07、NFR-01 至 NFR-02；等待 SPEC 驗收。 |
| TODO-002 | 建立 SDD + DDD + TDD + BDD SPEC 草案 | 已完成 | 2026-08-18 | 本文件 v0.1.0 已建立；等待需求方審核。 |
| TODO-003 | 需求方審核與驗收 SPEC | 已驗收 | 2026-08-18 | 需求方於 2026-08-18 明確確認「看起來沒問題，請開始實作」。 |
| TODO-004 | 確認執行環境與待定決策 | 已完成 | 2026-08-18 | 已採用 Selenium Manager、Pixel 7、`m.twitch.tv`、`artifacts/`、cookie/modal/App 開啟遮罩處理與「瀏覽」頁搜尋回退。 |
| TODO-005 | 建立測試專案與 DDD 邊界 | 已完成 | 2026-08-18 | 已建立 domain、application ports/orchestration、Selenium infrastructure、features 與測試分層。 |
| TODO-006 | 以 TDD 完成 unit/contract tests 與實作 | 已完成 | 2026-08-18 | 已恢復 Pixel 7（412×915）並擴充 Device Profile matrix unit test；快速測試 16/16 通過。 |
| TODO-007 | 以 BDD 完成 Chrome WAP E2E 驗收 | 已完成 | 2026-08-18 | `pytest -m e2e -n 3` 通過 3/3；Pixel 7、iPhone、Samsung 各以獨立 Chrome session 同時完成，並各自保留 Evidence。 |
| TODO-008 | 規格品質閘門範例 | 已驗收 | 2026-08-18 | 此列只驗收 TODO 狀態詞彙與欄位結構已依規則建立；**不代表產品 SPEC 或實作已驗收**。 |
| TODO-009 | SPEC 靜態一致性檢查 | 已完成 | 2026-08-18 | 已確認來源旅程、必要技術、DDD 邊界、BDD、TDD 節奏、實作閘門及四種 TODO 狀態均存在；等待需求方驗收。 |
| TODO-010 | 清理 SPEC 檢視暫存檔 | 已完成 | 2026-08-18 | 已移除僅用於 PDF 視覺檢視的本機 PNG 暫存檔；來源 PDF 與 SPEC 未受影響。 |
| TODO-011 | 需求方最終驗收實作 | 進行中 | 2026-08-18 | 三種 viewport 的 live E2E 已通過；等待需求方確認畫面與 batch 產物結構。僅需求方可更新為「已驗收」。 |
| TODO-012 | 建立多裝置與 Evidence Batch 產物策略 | 已完成 | 2026-08-18 | 平行實測 batch `20260818T154112634756Z-2503f424` 已含 `pixel-7/`、`iphone/`、`samsung/` 各一張 Evidence；三個 worker 共用同一 run-id。 |
| TODO-013 | 修正 linter error | 已完成 | 2026-08-19 | 已加入可重現的 Ruff 依賴與規則，修正 5 項靜態檢查錯誤；`ruff check src tests` 通過，快速測試 16/16 通過。 |
| TODO-014 | 完成 requirements、README GIF 與 Git 發布 | 已完成 | 2026-08-20 | `requirements.txt` 已列出全部依賴；README 已嵌入 5 幀本機 Pixel 7 E2E GIF；Ruff 與快速測試通過。實作已於 commit `ff3a538` 推送至 `origin/main`。 |

## 9. 變更紀錄

| 日期 | 版本 | 變更 | TODO 同步 |
| --- | --- | --- | --- |
| 2026-08-18 | 0.1.0 | 建立初版需求、DDD 邊界、BDD 情境、TDD/SDD 守則與實作閘門。 | TODO-001、TODO-002 更新為已完成；TODO-003 更新為進行中。 |
| 2026-08-18 | 0.1.0 | 開始執行 SPEC 靜態一致性檢查。 | TODO-009 更新為進行中。 |
| 2026-08-18 | 0.1.0 | 完成 SPEC 靜態一致性檢查，未建立任何產品、測試或 CI 實作。 | TODO-009 更新為已完成。 |
| 2026-08-18 | 0.1.0 | 開始清理 PDF 視覺檢視暫存檔。 | TODO-010 更新為進行中。 |
| 2026-08-18 | 0.1.0 | 完成清理 PDF 視覺檢視暫存檔。 | TODO-010 更新為已完成。 |
| 2026-08-18 | 0.2.0 | 需求方驗收 SPEC，解除實作閘門並開始執行環境決策及測試框架實作。 | TODO-003 更新為已驗收；TODO-004、TODO-005 更新為進行中。 |
| 2026-08-18 | 0.2.0 | 完成執行環境、DDD 分層與 TDD unit/contract 實作；快速測試通過，開始 live E2E 驗收。 | TODO-004 至 TODO-006 更新為已完成；TODO-007 更新為進行中。 |
| 2026-08-18 | 0.2.0 | 首次 live E2E 未通過；重新開啟失敗證據實作，補齊截圖與診斷 metadata 後再測。 | TODO-006 更新為進行中。 |
| 2026-08-18 | 0.2.0 | 依 live E2E 證據更新現行 WAP 搜尋入口與 App 開啟遮罩的相容性決策。 | TODO-004 更新為進行中。 |
| 2026-08-18 | 0.2.0 | 依 live E2E 證據釐清 FR-04：兩次捲動是動作要求；到達結果底部的後續動作不應誤判為失敗。 | TODO-007 維持進行中。 |
| 2026-08-18 | 0.2.0 | E2E 首次通過但截圖顯示選到導覽列的活動頁，判定為 false positive；重新開啟 FR-05/FR-06 驗收。 | TODO-007 維持進行中。 |
| 2026-08-18 | 0.2.0 | E2E 再次通過但截圖為空白，判定為 Channel Readiness 條件過寬；補齊頻道識別與截圖非空白品質檢查後重驗。 | TODO-006、TODO-007 維持進行中。 |
| 2026-08-18 | 0.3.0 | 完成現行 WAP 相容性、失敗診斷、頻道定位、頻道就緒及截圖品質修正；unit/contract 與 live BDD/E2E 均通過。 | TODO-004、TODO-006、TODO-007 更新為已完成；TODO-011 更新為進行中。 |
| 2026-08-18 | 0.3.1 | 需求方指出成功截圖播放器為純黑；撤回完成判定，將 FR-06 強化為非黑色實際畫格驗證並重新開啟修正。 | TODO-006、TODO-007 更新為進行中；TODO-011 更新為未開始。 |
| 2026-08-18 | 0.3.2 | 已加入 HTML5 video 可播放狀態與播放器區域像素檢查；畫格驗證後的 unit/contract 與 live E2E 均通過。 | TODO-006、TODO-007 更新為已完成；TODO-011 更新為進行中。 |
| 2026-08-18 | 0.3.2 | 依需求方審閱，確認現行 DOM 有頻道 metadata 與 `data-a-target="chat-input"`，但尚未將兩者的視覺可見性納入 E2E 截圖驗收。 | TODO-011 維持進行中。 |
| 2026-08-18 | 0.3.2 | 需求方要求將實況主名稱與聊天室輸入框納入手機證據驗收。 | TODO-006、TODO-007 更新為進行中。 |
| 2026-08-18 | 0.3.3 | 在乾淨 Pixel 7 Chrome 實測確認 Twitch 顯示登入控制項且未渲染 `chat-input`。將已登入專用 profile 與未登入可診斷失敗列為 FR-09 前置條件。 | TODO-006、TODO-007、TODO-011 維持進行中。 |
| 2026-08-18 | 0.3.4 | live E2E 再次確認未登入工作階段沒有 `chat-input`；登入提示以非標準控制項呈現，開始補強診斷偵測。 | TODO-006、TODO-007 維持進行中。 |
| 2026-08-18 | 0.3.5 | 確認捲到聊天室後仍不會延遲建立 `chat-input`。完成已登入／可聊天 profile 的設定與診斷實作；等待該 profile 進行 FR-09 live 驗收。 | TODO-006 更新為已完成；TODO-007、TODO-011 維持進行中。 |
| 2026-08-18 | 0.3.6 | 完成未設定 profile 的 live E2E 回歸：快速測試 18/18 通過；FR-09 以明確前置條件錯誤與失敗 Evidence 結束，未宣告為通過。 | TODO-007、TODO-011 維持進行中。 |
| 2026-08-18 | 0.3.7 | 需求方確認只需截圖與完整旅程，登入為 out of scope。撤回將聊天輸入框列為驗收條件的推論，回歸未登入 WAP Evidence。 | TODO-006、TODO-007、TODO-011 維持進行中。 |
| 2026-08-18 | 0.3.8 | 未登入 live E2E 已通過；快速層發現一個 contract fake 的已移除欄位參數，開始同步並重跑測試。 | TODO-006、TODO-007 維持進行中。 |
| 2026-08-18 | 0.3.9 | contract fake 已同步；快速測試 14/14 與未登入 Pixel 7 live E2E 1/1 均通過。 | TODO-006、TODO-007 更新為已完成；TODO-011 維持進行中。 |
| 2026-08-18 | 0.4.0 | 需求方要求保留實況主名稱但移除 metadata 造成的畫面變暗。開始實作僅透明化 backdrop 的 Evidence 呈現。 | TODO-006、TODO-007 更新為進行中；TODO-011 維持進行中。 |
| 2026-08-18 | 0.4.1 | 已透明化 metadata backdrop，並加入全 viewport backdrop 必須透明的明確等待驗證。快速測試 14/14 與 live E2E 1/1 均通過。 | TODO-006、TODO-007 更新為已完成；TODO-011 維持進行中。 |
| 2026-08-18 | 0.5.0 | 需求方要求 iPhone 與 Samsung viewport 可同時驗證，且所有產物依一次執行歸入同一資料夾。 | TODO-006、TODO-007、TODO-012 更新為進行中；TODO-011 維持進行中。 |
| 2026-08-18 | 0.5.1 | iPhone live E2E 已通過且 batch 結構正確；Samsung 實測發現窄 viewport 的「瀏覽」連結點擊會被 App 提示攔截，開始修正回退入口。 | TODO-006、TODO-007、TODO-012 維持進行中。 |
| 2026-08-18 | 0.5.2 | Samsung 安全點擊修正後單裝置 live E2E 通過。開始快速回歸及兩 worker 平行 E2E 驗收。 | TODO-006、TODO-007、TODO-012 維持進行中。 |
| 2026-08-18 | 0.5.3 | 快速測試 16/16 與兩 worker 平行 E2E 2/2 均通過；兩個裝置 Evidence 已寫入同一 batch 的各自子資料夾。 | TODO-006、TODO-007、TODO-012 更新為已完成；TODO-011 維持進行中。 |
| 2026-08-18 | 0.5.4 | 需求方指出原始 Pixel 7 不應被多裝置支援取代。開始恢復 Pixel 7 並擴充為三裝置矩陣。 | TODO-006、TODO-007、TODO-012 更新為進行中；TODO-011 維持進行中。 |
| 2026-08-18 | 0.5.5 | 快速測試 16/16 與三 worker 平行 E2E 3/3 均通過；Pixel 7、iPhone、Samsung Evidence 已寫入同一 batch 的各自子資料夾。 | TODO-006、TODO-007、TODO-012 更新為已完成；TODO-011 維持進行中。 |
| 2026-08-19 | 0.5.6 | 需求方要求修正 linter error，開始靜態檢查。 | TODO-013 更新為進行中；TODO-011 維持進行中。 |
| 2026-08-19 | 0.5.7 | 已加入 Ruff、修正 import 排序、`__all__` 排序與 mutable class attribute 註記；lint 與快速測試均通過。 | TODO-013 更新為已完成；TODO-011 維持進行中。 |
| 2026-08-20 | 0.5.8 | 需求方要求確認 `requirements.txt`、README 本機測試 GIF，並授權在驗證後 commit 與 push。 | TODO-014 更新為進行中；TODO-011 維持進行中。 |
| 2026-08-20 | 0.5.9 | 已確認依賴清單、產生並嵌入 5 幀本機 E2E GIF，且 Ruff 與快速測試通過；開始 Git 發布。 | TODO-014 維持進行中；TODO-011 維持進行中。 |
| 2026-08-20 | 0.6.0 | commit `ff3a538` 已成功推送至 `origin/main`；交付文件與發布完成。 | TODO-014 更新為已完成；TODO-011 維持進行中。 |

## 10. 審核結論（由需求方填寫）

- [x] 驗收本 SPEC v0.1.0，允許依 TODO-004 開始後續工作。
- [ ] 退回修訂；請於下方列出需要變更的需求、情境或架構原則。

審核意見：

> 
