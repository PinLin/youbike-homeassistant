DOMAIN = "youbike"
CONF_STATION_ID = "station_id"
CONF_CITY = "city"
CONF_SCAN_INTERVAL = "scan_interval"
SERVICE_UPDATE = "update"
EVENT_UPDATED = "youbike_updated"

# YouBike Official Website API endpoints (publicly accessible, no auth required)
YOUBIKE_WEBSITE_STATION_URL = "https://apis.youbike.com.tw/json/station-min-yb2.json"
YOUBIKE_WEBSITE_PARKING_URL = "https://apis.youbike.com.tw/tw2/parkingInfo"
YOUBIKE_WEBSITE_AREA_URL = "https://apis.youbike.com.tw/json/area-all.json"

# All cities supported via Official Website API
WEBSITE_AVAILABLE_CITIES: dict[str, str] = {
    "Taipei":             "台北市",
    "NewTaipei":          "新北市",
    "Taoyuan":            "桃園市",
    "Taichung":           "台中市",
    "Tainan":             "臺南市",
    "Kaohsiung":          "高雄市",
    "Hsinchu":            "新竹市",
    "HsinchuSciencePark": "新竹科學工業園區",
    "Chiayi":             "嘉義市",
    "HsinchuCounty":      "新竹縣",
    "MiaoliCounty":       "苗栗縣",
    "ChiayiCounty":       "嘉義縣",
    "PingtungCounty":     "屏東縣",
    "TaitungCounty":      "臺東縣",
    "Guangfu":            "光復鄉（花蓮）",
}

# Map CONF_CITY → area_code (hex from area-all.json) for station list filtering
CITY_TO_WEBSITE_AREA_CODE: dict[str, str] = {
    "Taipei":             "00",
    "NewTaipei":          "05",
    "Taoyuan":            "07",
    "Taichung":           "01",
    "Tainan":             "13",
    "Kaohsiung":          "12",
    "Hsinchu":            "09",
    "Chiayi":             "08",
    "HsinchuCounty":      "0B",
    "HsinchuSciencePark": "10",
    "MiaoliCounty":       "0A",
    "ChiayiCounty":       "11",
    "PingtungCounty":     "14",
    "TaitungCounty":      "15",
    "Guangfu":            "16",
}

# UID prefix for website source (city → short prefix, no underscores)
CITY_TO_WEBSITE_UID_PREFIX: dict[str, str] = {
    "Taipei":             "TPE",
    "NewTaipei":          "NWT",
    "Taoyuan":            "TYN",
    "Taichung":           "TXG",
    "Tainan":             "TNN",
    "Kaohsiung":          "KHH",
    "Hsinchu":            "HSZ",
    "Chiayi":             "CYI",
    "HsinchuCounty":      "HSC",
    "HsinchuSciencePark": "HSP",
    "MiaoliCounty":       "MIL",
    "ChiayiCounty":       "CYC",
    "PingtungCounty":     "PTC",
    "TaitungCounty":      "TTT",
    "Guangfu":            "GFU",
}

DEFAULT_SCAN_INTERVAL = 300  # seconds; 0 means manual-only

# Reverse map: uid_prefix → area_code (derived from CITY_TO_WEBSITE_UID_PREFIX + CITY_TO_WEBSITE_AREA_CODE)
UID_PREFIX_TO_AREA_CODE: dict[str, str] = {
    v: CITY_TO_WEBSITE_AREA_CODE[k]
    for k, v in CITY_TO_WEBSITE_UID_PREFIX.items()
}

STATION_CACHE_TTL = 86400  # seconds, 24 hours
