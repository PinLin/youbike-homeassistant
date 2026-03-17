# YouBike Integration for Home Assistant

Home Assistant 自訂整合元件，即時監控 YouBike 站點車輛與車位數量。

## 功能

- 監控一般自行車、電動輔助自行車可借數量、可還空位與營運狀態
- 資料來源：官網 API（非正式，無需認證）
- 支援 15 個城市／區域（台北、新北、桃園、台中、台南、高雄、新竹市、嘉義市、新竹縣、苗栗縣、嘉義縣、屏東縣、臺東縣、新竹科學工業園區、光復鄉）
- 每個站點各自設定更新間隔（秒），完全獨立運作

## 安裝

### HACS（推薦）

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PinLin&repository=youbike-homeassistant&category=integration)

1. 在 HACS 中選擇「自訂存放庫」
2. 輸入 `https://github.com/PinLin/youbike-homeassistant`，類別選擇「Integration」
3. 安裝後重啟 Home Assistant

### 手動安裝

將 `custom_components/youbike/` 複製到 Home Assistant 的 `custom_components/` 目錄下，重啟。

## 設定

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=youbike)

前往 **設定 → 裝置與服務 → 新增整合 → YouBike**，選擇城市、輸入關鍵字搜尋後選取站點，設定更新間隔。每個站點為獨立的整合條目，可分別設定不同的更新頻率。

## 建立的實體

每個站點建立 5 個實體：

| 實體 | 說明 |
|------|------|
| 自行車數量 | 可借一般自行車數 |
| 電輔車數量 | 可借電動輔助自行車數 |
| 可還空位 | 可還車位數 |
| 資料更新時間 | 最後抓取時間 |
| 營運狀態 | 場站是否營運中（binary sensor） |

entity_id 格式：`sensor.{UID}_{屬性}`，例如 `sensor.tpe500101001_general_bikes`。

## 站點 UID

格式：`{城市前綴}{站號}`，例如 `TPE500101001`、`KHH501208057`。

## 服務

### `youbike.update`

手動觸發更新。可指定 `station_ids` 清單只更新特定站點，留空則更新全部。

## 授權

MIT License
