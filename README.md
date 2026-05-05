# YouBike Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/PinLin/youbike-homeassistant.svg?style=flat-square)](https://github.com/PinLin/youbike-homeassistant/releases)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

將 YouBike 站點即時資訊整合到 Home Assistant，隨時掌握附近站點的可用車輛與空位數量。

## 功能特色

- **即時數量監控**：監控一般自行車、電動輔助自行車可借數量、可還空位與營運狀態。
- **多城市支援**：支援 15 個城市／區域（台北、新北、桃園、台中、台南、高雄、新竹市、嘉義市、新竹縣、苗栗縣、嘉義縣、屏東縣、臺東縣、新竹科學工業園區、光復鄉（花蓮））。
- **多站點管理**：每個站點為獨立的整合條目，可分別設定不同的更新頻率。
- **手動更新服務**：提供 `youbike.update`，可更新全部站點或指定 `station_ids`。

## 安裝方式

### HACS（推薦）

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PinLin&repository=youbike-homeassistant&category=integration)

1. 在 HACS 中選擇「自訂存放庫」
2. 輸入 `https://github.com/PinLin/youbike-homeassistant`，類別選擇「Integration」
3. 安裝後重啟 Home Assistant

### 手動安裝

將 `custom_components/youbike/` 複製到 Home Assistant 的 `custom_components/` 目錄下，重啟。

## 設定

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=youbike)

前往 **設定 → 裝置與服務 → 新增整合 → YouBike**，選擇城市並輸入關鍵字搜尋後選取站點，設定更新間隔。

## 建立的實體

每個站點建立 5 個實體：

| 實體 | 說明 |
|------|------|
| 自行車數量 | 可借一般自行車數 |
| 電輔車數量 | 可借電動輔助自行車數 |
| 可還空位 | 可還車位數 |
| 資料更新時間 | 最後抓取時間 |
| 營運狀態 | 場站是否營運中（binary sensor） |

`entity_id` 格式會加上 `youbike` 前綴，例如：

```text
sensor.youbike_tpe500101001_general_bikes
binary_sensor.youbike_tpe500101001_service_status
```

## 站點 UID

格式：`{城市前綴}{站號}`，例如 `TPE500101001`、`KHH501208057`。

站點 UID 也會顯示在：

- 裝置型號欄位
- 實體屬性 `station_id`

## 服務

### `youbike.update`

手動觸發更新。可指定 `station_ids` 清單只更新特定站點，留空則更新全部。

```yaml
service: youbike.update
data:
  station_ids:
    - NWT500218121
```

## 疑難排解

### 站點數據沒有更新
1. 確認 Home Assistant 的網路可以正常連到外部。YouBike 官方站點 API 為非官方介面，偶爾會短暫失敗；本整合會自動重試，連續多次失敗會在**設定** > **修復**中顯示通知。
2. 在**設定** > **裝置與服務** > **YouBike**將更新間隔調短，重新拉一次資料。
3. 透過 `youbike.update` 服務手動觸發更新。

### 想看更詳細的紀錄
在 `configuration.yaml` 加入：

```yaml
logger:
  logs:
    custom_components.youbike: debug
```

重啟後，相關紀錄會出現在 Home Assistant 的系統紀錄中。

### 提交 Issue
請在**設定** > **裝置與服務** > **YouBike** > 三個點 > **下載診斷資料**取得 JSON，連同 Home Assistant 版本與重現步驟一起附上，能大幅縮短排查時間。

## 移除整合

1. 前往**設定** > **裝置與服務**。
2. 點選 **YouBike** 整合卡片中要移除的站點。
3. 點選右上角三個點 > **刪除**。
4. 若不再需要本整合的程式碼，可在**HACS**中將其移除，或手動刪除 `config/custom_components/youbike/` 資料夾。

## 免責聲明

本整合為非官方、社群維護的專案，與微笑單車股份有限公司無任何關係。資料來源為 YouBike 官網公開的網頁 API；該介面為非官方端點，可能在沒有預告的情況下變更或停用。

## 授權

MIT License
