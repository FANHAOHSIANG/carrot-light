# Carrot Light — Ioniq 5 / EV6 車況連動氛圍燈

`main` 保存氛圍燈附加程式、ESP32 韌體與安裝入口；`carrot-wip` 由工作流程建立完整可安裝車端原始碼。基底固定為官方 ajouatom/openpilot carrot-wip 的 e74e6938ddc4574b1ba19ee7405ff146f3c1728e，這不是自動追蹤上游更新的分支。

## C4 安裝

必須先確認 Actions 的 Build installable Carrot Light 成功，而且 carrot-wip 分支存在。透過 C4「自訂軟體」輸入：

```
https://raw.githubusercontent.com/FANHAOHSIANG/carrot-light/main/installer.sh
```

此為提供給 comma 自訂軟體安裝器的 shell 腳本；不是瀏覽器網頁，也不是 ESP32 韌體。已裝有 Carrotpilot 的 C4 需走裝置正常卸載／重新安裝流程才能使用；此腳本不會刪除既有 /data/openpilot。安裝程序與原生 build 尚待 C4 實機驗證，請勿行駛中操作。

## C4 端行為

manager 在 only_onroad 狀態啟動 ambient_light（不需要啟用巡航）。它只讀取 carState，不發送 CAN 或修改控制；將左右方向燈、煞車踏板與左右盲點旗標，以 20Hz、16-byte UDP 傳送至 ESP32。

沒有 /data/ambient_light/config.json 時，預設使用本地 IPv4 廣播 255.255.255.255:7799、測試 token 324508639、踩踏板模式。C4 與 ESP32 必須在同一區域網路，路由器不能隔離客戶端；某些手機熱點可能阻擋廣播，需改成 ESP32 的固定 IP。不要把此埠開放至網際網路。token 只是避免收錯封包，不是加密或正式認證。

如需固定 IP 或更改 token，在 C4 建立 /data/ambient_light/config.json，格式見 comma/config.example.json。既有設定會優先使用；重啟行車程序後生效。ESP32 的 token 必須一致。

超過 300ms 未收到 carState、valid=false 或 canValid=false，傳送端清除警示；ESP32 超過 500ms 收不到封包，也回到普通氛圍狀態。方向燈閃爍由 ESP32 產生，不保證與車外燈每次亮滅同相。

brake_mode 預設 pedal：使用 brakePressed。lights 使用 brakeLights，但官方 Hyundai CAN-FD 這個欄位也包含 aEgo<-0.5 的減速推估，不能視為實體煞車燈完全同步。盲點欄位存在不代表你的配備與解析一定可用，仍需確認實車資料。

## ESP32 與桌上測試

Arduino IDE 開啟 esp32/ambient_receiver/ambient_receiver.ino，先設定 Wi-Fi SSID/密碼，選擇正確 ESP32 板型並以 USB 上傳。它不是透過 C4 安裝網址更新。

預設 ENABLE_LEDS=0：先用 115200 序列埠驗證收訊，不需要 FastLED。電腦與 ESP32 同網路時執行：

```sh
python3 comma/bench_send.py --ip ESP32的IP
```

燈条型號與電壓尚未確認。ENABLE_LEDS=1 的程式只示範 WS2812B，GPIO4/60燈是示例，不能直接当成已確認接線。需確認板型、GPIO、燈条晶片/色序/電壓與燈珠數量，再設定 FastLED。獨立供電、保險絲與電位轉換依實際硬體規格處理。

## 驗證與限制

桌面測試涵蓋警示清除、踏板與回生模式區別、預設廣播設定、封包與序號回繞、安裝/卸載可重複及保留其他修改。尚未進行 Arduino 編譯、C4 原生編譯、實機 manager、Wi-Fi 廣播與實車車況驗證。調光網頁尚未加入。

工作流程是一次性建立 carrot-wip；若該分支已存在會停止，避免覆蓋你後來的修改。未設定排程或自動同步官方。要更新基底，需建立新版本並重新驗證。

官方完整來源的授權資訊與 LICENSE 保留於 carrot-wip；本工具僅擴充燈光顯示。
