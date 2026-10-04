#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_PWMServoDriver.h>

// ============================================================
// WIFI SETTINGS
// ============================================================

const char* WIFI_SSID = "KPS";
const char* WIFI_PASSWORD = "kachra.polash";

WebServer server(80);

// ============================================================
// PCA9685
// ============================================================

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define SDA_PIN 21
#define SCL_PIN 22

#define SERVO_FREQ 50

#define SERVOMIN 102
#define SERVOMAX 512

// ============================================================
// SERVO CHANNELS
// ============================================================

#define SERVO1_CH 0
#define SERVO2_CH 1
#define SERVO3_CH 2
#define SERVO4_CH 3
#define SERVO5_CH 4

// ============================================================
// SERVO LIMITS
// ============================================================

const int SERVO1_MIN = 80;
const int SERVO1_MAX = 180;

const int SERVO2_MIN = 0;
const int SERVO2_MAX = 100;

const int SERVO3_MIN = 80;
const int SERVO3_MAX = 180;

const int SERVO4_MIN = 30;
const int SERVO4_MAX = 130;

const int SERVO5_MIN = 80;
const int SERVO5_MAX = 180;

// ============================================================
// CURRENT ANGLES
// ============================================================

int servoAngles[5] = {
  90, 90, 90, 90, 90
};

// ============================================================
// AUTO CYCLE SETTINGS
// ============================================================

// MIN -> MAX takes 1 second
// MAX -> MIN takes 1 second

const unsigned long CYCLE_DURATION = 1000;

// Servo update interval
const unsigned long CYCLE_UPDATE_INTERVAL = 30;

// Small pause at maximum/minimum
const unsigned long END_PAUSE = 100;

// Small center pause
const unsigned long CENTER_PAUSE = 100;

// Small minimum pause
const unsigned long MIN_PAUSE = 100;

bool autoCycleRunning = false;

// ============================================================
// AUTO PHASES
// ============================================================

enum AutoPhase {
  AUTO_IDLE,
  AUTO_CENTER,
  AUTO_TO_MIN,
  AUTO_MIN_TO_MAX,
  AUTO_PAUSE_AFTER_MAX,
  AUTO_MAX_TO_MIN,
  AUTO_PAUSE_AFTER_MIN
};

AutoPhase autoPhase = AUTO_IDLE;

unsigned long autoPhaseStart = 0;
unsigned long lastCycleUpdate = 0;


// ============================================================
// HTML
// ============================================================

const char index_html[] PROGMEM = R"rawliteral(

<!DOCTYPE html>

<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>5-Finger Servo Hand</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f2f4f7;
    color: #222;
}

.container {
    max-width: 650px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 20px;
}

.status-box,
.control-box {
    background: white;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.status {
    display: flex;
    align-items: center;
    gap: 10px;
}

.status-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #28a745;
}

.status-text {
    font-weight: bold;
}

.finger-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.finger-name {
    font-size: 18px;
    font-weight: bold;
}

.angle {
    font-size: 20px;
    font-weight: bold;
}

.range {
    color: #777;
    font-size: 13px;
    margin: 8px 0 12px;
}

input[type=range] {
    width: 100%;
    cursor: pointer;
}

.buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

button {
    border: none;
    border-radius: 10px;
    padding: 15px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

.center-btn {
    background: #007bff;
    color: white;
}

.auto-btn {
    background: #28a745;
    color: white;
}

.auto-btn.running {
    background: #ff9800;
}

.stop-btn {
    background: #dc3545;
    color: white;
    grid-column: 1 / 3;
}

button:active {
    transform: scale(0.98);
}

.info {
    text-align: center;
    color: #666;
    font-size: 13px;
    margin-top: 15px;
}

@media(max-width: 500px) {

    body {
        padding: 10px;
    }

    .buttons {
        grid-template-columns: 1fr;
    }

    .stop-btn {
        grid-column: 1;
    }

}

</style>

</head>

<body>

<div class="container">

<h1>🤖 5-Finger Servo Hand</h1>

<div class="subtitle">
ESP32 + PCA9685 Controller
</div>


<!-- ===================================================== -->
<!-- STATUS -->
<!-- ===================================================== -->

<div class="status-box">

<div class="status">

<div id="statusDot" class="status-dot"></div>

<div id="statusText" class="status-text">
Connecting...
</div>

</div>

<div id="autoStatus" style="margin-top:8px;">
Manual Mode
</div>

</div>


<!-- ===================================================== -->
<!-- FINGER 1 -->
<!-- ===================================================== -->

<div class="control-box">

<div class="finger-title">

<div class="finger-name">
Finger 1
</div>

<div class="angle">
<span id="angle1">90</span>°
</div>

</div>

<div class="range">
Range: 80° - 180°
</div>

<input
id="slider1"
type="range"
min="80"
max="180"
value="90"
oninput="sliderChanged(1,this.value)"
>

</div>


<!-- ===================================================== -->
<!-- FINGER 2 -->
<!-- ===================================================== -->

<div class="control-box">

<div class="finger-title">

<div class="finger-name">
Finger 2
</div>

<div class="angle">
<span id="angle2">90</span>°
</div>

</div>

<div class="range">
Range: 0° - 100°
</div>

<input
id="slider2"
type="range"
min="0"
max="100"
value="90"
oninput="sliderChanged(2,this.value)"
>

</div>


<!-- ===================================================== -->
<!-- FINGER 3 -->
<!-- ===================================================== -->

<div class="control-box">

<div class="finger-title">

<div class="finger-name">
Finger 3
</div>

<div class="angle">
<span id="angle3">90</span>°
</div>

</div>

<div class="range">
Range: 80° - 180°
</div>

<input
id="slider3"
type="range"
min="80"
max="180"
value="90"
oninput="sliderChanged(3,this.value)"
>

</div>


<!-- ===================================================== -->
<!-- FINGER 4 -->
<!-- ===================================================== -->

<div class="control-box">

<div class="finger-title">

<div class="finger-name">
Finger 4
</div>

<div class="angle">
<span id="angle4">90</span>°
</div>

</div>

<div class="range">
Range: 30° - 130°
</div>

<input
id="slider4"
type="range"
min="30"
max="130"
value="90"
oninput="sliderChanged(4,this.value)"
>

</div>


<!-- ===================================================== -->
<!-- FINGER 5 -->
<!-- ===================================================== -->

<div class="control-box">

<div class="finger-title">

<div class="finger-name">
Finger 5
</div>

<div class="angle">
<span id="angle5">90</span>°
</div>

</div>

<div class="range">
Range: 80° - 180°
</div>

<input
id="slider5"
type="range"
min="80"
max="180"
value="90"
oninput="sliderChanged(5,this.value)"
>

</div>


<!-- ===================================================== -->
<!-- BUTTONS -->
<!-- ===================================================== -->

<div class="control-box">

<div class="buttons">

<button
class="center-btn"
onclick="centerAll()">
CENTER ALL
</button>

<button
id="autoButton"
class="auto-btn"
onclick="toggleAuto()">
AUTO CYCLE
</button>

<button
class="stop-btn"
onclick="emergencyStop()">
EMERGENCY STOP
</button>

</div>

</div>


<div class="info">

Connected through Wi-Fi router<br>

ESP32 IP:
<b id="ipAddress">...</b>

</div>

</div>


<script>

// ============================================================
// GLOBAL VARIABLES
// ============================================================

let autoRunning = false;

let sendTimers = {};

// Prevent multiple position requests
let positionRequestRunning = false;


// ============================================================
// SEND COMMAND
// ============================================================

function sendCommand(command)
{

    fetch(
        "/command?cmd=" +
        encodeURIComponent(command),
        {
            cache: "no-store"
        }
    )

    .then(response =>
        response.text()
    )

    .then(data =>
    {
        console.log(data);
    })

    .catch(error =>
    {
        console.log(
            "Command error:",
            error
        );
    });

}


// ============================================================
// SLIDER
// ============================================================

function sliderChanged(
    servo,
    value
)
{

    // Immediately update displayed angle

    document.getElementById(
        "angle" + servo
    ).innerText = value;


    // Do not send manual command
    // while auto cycle is running

    if(autoRunning)
        return;


    clearTimeout(
        sendTimers[servo]
    );


    sendTimers[servo] =
        setTimeout(
            function()
            {

                sendCommand(
                    "S" +
                    servo +
                    ":" +
                    value
                );

            },
            40
        );

}


// ============================================================
// CENTER ALL
// ============================================================

function centerAll()
{

    sendCommand(
        "CENTER"
    );

}


// ============================================================
// AUTO CYCLE
// ============================================================

function toggleAuto()
{

    if(autoRunning)
    {

        sendCommand(
            "STOP"
        );

    }

    else
    {

        sendCommand(
            "AUTO"
        );

    }

}


// ============================================================
// EMERGENCY STOP
// ============================================================

function emergencyStop()
{

    sendCommand(
        "STOP"
    );

}


// ============================================================
// UPDATE POSITION
//
// IMPORTANT:
// Only ONE position request is allowed at a time.
// This prevents browser request stacking.
// ============================================================

function updatePositions()
{

    if(positionRequestRunning)
        return;


    positionRequestRunning = true;


    fetch(
        "/position",
        {
            cache: "no-store"
        }
    )

    .then(response =>
        response.json()
    )

    .then(data =>
    {

        // ----------------------------------------------------
        // AUTO STATUS
        // ----------------------------------------------------

        autoRunning =
            data.auto;


        // ----------------------------------------------------
        // UPDATE ALL SLIDERS
        // ----------------------------------------------------

        for(
            let i = 0;
            i < 5;
            i++
        )
        {

            let n =
                i + 1;

            let angle =
                data.angles[i];


            document.getElementById(
                "slider" + n
            ).value =
                angle;


            document.getElementById(
                "angle" + n
            ).innerText =
                angle;

        }


        // ----------------------------------------------------
        // BUTTON
        // ----------------------------------------------------

        let button =
            document.getElementById(
                "autoButton"
            );


        let status =
            document.getElementById(
                "autoStatus"
            );


        if(autoRunning)
        {

            button.innerText =
                "STOP AUTO CYCLE";


            button.classList.add(
                "running"
            );


            status.innerText =
                "🔄 Auto Cycle Running";

        }

        else
        {

            button.innerText =
                "AUTO CYCLE";


            button.classList.remove(
                "running"
            );


            status.innerText =
                "Manual Mode";

        }


        // ----------------------------------------------------
        // CONNECTION STATUS
        // ----------------------------------------------------

        document.getElementById(
            "statusText"
        ).innerText =
            "Connected";


        document.getElementById(
            "statusDot"
        ).style.background =
            "#28a745";

    })

    .catch(error =>
    {

        console.log(
            "Position error:",
            error
        );


        document.getElementById(
            "statusText"
        ).innerText =
            "Connection Lost";


        document.getElementById(
            "statusDot"
        ).style.background =
            "#dc3545";

    })

    .finally(() =>
    {

        positionRequestRunning =
            false;

    });

}


// ============================================================
// UPDATE POSITION EVERY 80ms
// ============================================================

setInterval(
    updatePositions,
    80
);


updatePositions();


// ============================================================
// SHOW ESP32 IP
// ============================================================

document.getElementById(
    "ipAddress"
).innerText =
    window.location.hostname;

</script>

</body>

</html>

)rawliteral";


// ============================================================
// ANGLE -> PWM
// ============================================================

uint16_t angleToPulse(
  int angle
)
{

  angle =
    constrain(
      angle,
      0,
      180
    );


  return map(
    angle,
    0,
    180,
    SERVOMIN,
    SERVOMAX
  );

}


// ============================================================
// WRITE SERVO
// ============================================================

void writeServo(
  int servoNumber,
  int angle
)
{

  int channel;


  switch(servoNumber)
  {

    case 1:

      channel =
        SERVO1_CH;

      angle =
        constrain(
          angle,
          SERVO1_MIN,
          SERVO1_MAX
        );

      break;


    case 2:

      channel =
        SERVO2_CH;

      angle =
        constrain(
          angle,
          SERVO2_MIN,
          SERVO2_MAX
        );

      break;


    case 3:

      channel =
        SERVO3_CH;

      angle =
        constrain(
          angle,
          SERVO3_MIN,
          SERVO3_MAX
        );

      break;


    case 4:

      channel =
        SERVO4_CH;

      angle =
        constrain(
          angle,
          SERVO4_MIN,
          SERVO4_MAX
        );

      break;


    case 5:

      channel =
        SERVO5_CH;

      angle =
        constrain(
          angle,
          SERVO5_MIN,
          SERVO5_MAX
        );

      break;


    default:

      return;

  }


  servoAngles[
    servoNumber - 1
  ] =
    angle;


  pwm.setPWM(
    channel,
    0,
    angleToPulse(angle)
  );

}


// ============================================================
// CENTER ALL SERVOS
// ============================================================

void centerAllServos()
{

  for(
    int i = 1;
    i <= 5;
    i++
  )
  {

    writeServo(
      i,
      90
    );

  }

}


// ============================================================
// GET SERVO MIN
// ============================================================

int getServoMin(
  int servo
)
{

  if(servo == 1)
    return SERVO1_MIN;

  if(servo == 2)
    return SERVO2_MIN;

  if(servo == 3)
    return SERVO3_MIN;

  if(servo == 4)
    return SERVO4_MIN;

  if(servo == 5)
    return SERVO5_MIN;


  return 0;

}


// ============================================================
// GET SERVO MAX
// ============================================================

int getServoMax(
  int servo
)
{

  if(servo == 1)
    return SERVO1_MAX;

  if(servo == 2)
    return SERVO2_MAX;

  if(servo == 3)
    return SERVO3_MAX;

  if(servo == 4)
    return SERVO4_MAX;

  if(servo == 5)
    return SERVO5_MAX;


  return 180;

}


// ============================================================
// MOVE ALL TO MIN
// ============================================================

void moveAllToMin()
{

  for(
    int i = 1;
    i <= 5;
    i++
  )
  {

    writeServo(
      i,
      getServoMin(i)
    );

  }

}


// ============================================================
// MOVE ALL TO MAX
// ============================================================

void moveAllToMax()
{

  for(
    int i = 1;
    i <= 5;
    i++
  )
  {

    writeServo(
      i,
      getServoMax(i)
    );

  }

}


// ============================================================
// START AUTO CYCLE
// ============================================================

void startAutoCycle()
{

  Serial.println(
    "AUTO_START"
  );


  autoCycleRunning =
    true;


  autoPhase =
    AUTO_CENTER;


  autoPhaseStart =
    millis();


  lastCycleUpdate =
    millis();


  centerAllServos();

}


// ============================================================
// STOP AUTO CYCLE
// ============================================================

void stopAutoCycle()
{

  autoCycleRunning =
    false;


  autoPhase =
    AUTO_IDLE;


  centerAllServos();


  Serial.println(
    "AUTO_STOPPED"
  );

}


// ============================================================
// AUTO CYCLE
// ============================================================

void updateAutoCycle()
{

  if(!autoCycleRunning)
    return;


  unsigned long now =
    millis();


  // ========================================================
  // CENTER
  // ========================================================

  if(
    autoPhase ==
    AUTO_CENTER
  )
  {

    if(
      now - autoPhaseStart >=
      CENTER_PAUSE
    )
    {

      moveAllToMin();


      autoPhase =
        AUTO_TO_MIN;


      autoPhaseStart =
        now;

    }


    return;

  }


  // ========================================================
  // MIN HOLD
  // ========================================================

  if(
    autoPhase ==
    AUTO_TO_MIN
  )
  {

    if(
      now - autoPhaseStart >=
      MIN_PAUSE
    )
    {

      autoPhase =
        AUTO_MIN_TO_MAX;


      autoPhaseStart =
        now;


      lastCycleUpdate =
        now;

    }


    return;

  }


  // ========================================================
  // MIN -> MAX
  // ========================================================

  if(
    autoPhase ==
    AUTO_MIN_TO_MAX
  )
  {

    if(
      now - lastCycleUpdate >=
      CYCLE_UPDATE_INTERVAL
    )
    {

      lastCycleUpdate =
        now;


      unsigned long elapsed =
        now - autoPhaseStart;


      // ----------------------------------------------------
      // END OF MOVEMENT
      // ----------------------------------------------------

      if(
        elapsed >=
        CYCLE_DURATION
      )
      {

        moveAllToMax();


        autoPhase =
          AUTO_PAUSE_AFTER_MAX;


        autoPhaseStart =
          now;


        return;

      }


      // ----------------------------------------------------
      // CALCULATE PROGRESS
      // ----------------------------------------------------

      float progress =
        (float)elapsed /
        (float)CYCLE_DURATION;


      // ----------------------------------------------------
      // MOVE ALL SERVOS
      // ----------------------------------------------------

      for(
        int i = 1;
        i <= 5;
        i++
      )
      {

        int minA =
          getServoMin(i);


        int maxA =
          getServoMax(i);


        int angle =
          minA +
          (int)(
            (maxA - minA) *
            progress
          );


        writeServo(
          i,
          angle
        );

      }

    }


    return;

  }


  // ========================================================
  // PAUSE AFTER MAX
  // ========================================================

  if(
    autoPhase ==
    AUTO_PAUSE_AFTER_MAX
  )
  {

    if(
      now - autoPhaseStart >=
      END_PAUSE
    )
    {

      autoPhase =
        AUTO_MAX_TO_MIN;


      autoPhaseStart =
        now;


      lastCycleUpdate =
        now;

    }


    return;

  }


  // ========================================================
  // MAX -> MIN
  // ========================================================

  if(
    autoPhase ==
    AUTO_MAX_TO_MIN
  )
  {

    if(
      now - lastCycleUpdate >=
      CYCLE_UPDATE_INTERVAL
    )
    {

      lastCycleUpdate =
        now;


      unsigned long elapsed =
        now - autoPhaseStart;


      // ----------------------------------------------------
      // END OF MOVEMENT
      // ----------------------------------------------------

      if(
        elapsed >=
        CYCLE_DURATION
      )
      {

        moveAllToMin();


        autoPhase =
          AUTO_PAUSE_AFTER_MIN;


        autoPhaseStart =
          now;


        return;

      }


      // ----------------------------------------------------
      // CALCULATE PROGRESS
      // ----------------------------------------------------

      float progress =
        (float)elapsed /
        (float)CYCLE_DURATION;


      // ----------------------------------------------------
      // MOVE ALL SERVOS
      // ----------------------------------------------------

      for(
        int i = 1;
        i <= 5;
        i++
      )
      {

        int minA =
          getServoMin(i);


        int maxA =
          getServoMax(i);


        int angle =
          maxA -
          (int)(
            (maxA - minA) *
            progress
          );


        writeServo(
          i,
          angle
        );

      }

    }


    return;

  }


  // ========================================================
  // PAUSE AFTER MIN
  // ========================================================

  if(
    autoPhase ==
    AUTO_PAUSE_AFTER_MIN
  )
  {

    if(
      now - autoPhaseStart >=
      END_PAUSE
    )
    {

      autoPhase =
        AUTO_MIN_TO_MAX;


      autoPhaseStart =
        now;


      lastCycleUpdate =
        now;

    }

  }

}


// ============================================================
// POSITION JSON
// ============================================================

void handlePosition()
{

  String json =
    "{";


  json +=
    "\"angles\":[";


  for(
    int i = 0;
    i < 5;
    i++
  )
  {

    json +=
      String(
        servoAngles[i]
      );


    if(i < 4)
      json += ",";

  }


  json +=
    "],";


  json +=
    "\"auto\":";


  json +=
    autoCycleRunning
    ? "true"
    : "false";


  json +=
    "}";


  server.send(
    200,
    "application/json",
    json
  );

}


// ============================================================
// COMMAND HANDLER
// ============================================================

void handleCommand()
{

  if(
    !server.hasArg("cmd")
  )
  {

    server.send(
      400,
      "text/plain",
      "Missing command"
    );

    return;

  }


  String command =
    server.arg("cmd");


  Serial.print(
    "Command: "
  );

  Serial.println(
    command
  );


  // ========================================================
  // CENTER
  // ========================================================

  if(
    command ==
    "CENTER"
  )
  {

    autoCycleRunning =
      false;


    autoPhase =
      AUTO_IDLE;


    centerAllServos();


    server.send(
      200,
      "text/plain",
      "CENTERED"
    );


    return;

  }


  // ========================================================
  // AUTO
  // ========================================================

  if(
    command ==
    "AUTO"
  )
  {

    if(!autoCycleRunning)
    {
      startAutoCycle();
    }


    server.send(
      200,
      "text/plain",
      "AUTO_STARTED"
    );


    return;

  }


  // ========================================================
  // STOP
  // ========================================================

  if(
    command ==
    "STOP"
  )
  {

    stopAutoCycle();


    server.send(
      200,
      "text/plain",
      "AUTO_STOPPED"
    );


    return;

  }


  // ========================================================
  // MANUAL SERVO
  // ========================================================

  if(
    command.startsWith("S")
  )
  {

    if(autoCycleRunning)
    {

      server.send(
        200,
        "text/plain",
        "AUTO_RUNNING"
      );


      return;

    }


    int colon =
      command.indexOf(':');


    if(colon > 0)
    {

      int servoNumber =
        command.substring(
          1,
          colon
        ).toInt();


      int angle =
        command.substring(
          colon + 1
        ).toInt();


      if(
        servoNumber >= 1 &&
        servoNumber <= 5
      )
      {

        writeServo(
          servoNumber,
          angle
        );


        server.send(
          200,
          "text/plain",
          "OK"
        );


        return;

      }

    }

  }


  // ========================================================
  // INVALID COMMAND
  // ========================================================

  server.send(
    400,
    "text/plain",
    "Invalid command"
  );

}


// ============================================================
// ROOT
// ============================================================

void handleRoot()
{

  server.send_P(
    200,
    "text/html",
    index_html
  );

}


// ============================================================
// 404
// ============================================================

void handleNotFound()
{

  server.send(
    404,
    "text/plain",
    "Not Found"
  );

}


// ============================================================
// WIFI CONNECTION
// ============================================================

void connectToWiFi()
{

  Serial.println();

  Serial.println(
    "=============================="
  );

  Serial.println(
    "Connecting to Wi-Fi..."
  );

  Serial.println(
    "=============================="
  );


  Serial.print(
    "SSID: "
  );

  Serial.println(
    WIFI_SSID
  );


  WiFi.mode(
    WIFI_STA
  );


  WiFi.setAutoReconnect(
    true
  );


  WiFi.persistent(
    false
  );


  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );


  int attempts =
    0;


  while(
    WiFi.status() !=
    WL_CONNECTED &&
    attempts < 40
  )
  {

    delay(500);


    Serial.print(
      "."
    );


    attempts++;

  }


  Serial.println();


  // ========================================================
  // CONNECTED
  // ========================================================

  if(
    WiFi.status() ==
    WL_CONNECTED
  )
  {

    Serial.println();

    Serial.println(
      "Wi-Fi CONNECTED!"
    );


    Serial.print(
      "IP Address: "
    );


    Serial.println(
      WiFi.localIP()
    );


    Serial.print(
      "Signal RSSI: "
    );


    Serial.print(
      WiFi.RSSI()
    );


    Serial.println(
      " dBm"
    );


    Serial.println();


    Serial.println(
      "Open this address in your browser:"
    );


    Serial.print(
      "http://"
    );


    Serial.println(
      WiFi.localIP()
    );

  }

  // ========================================================
  // FAILED
  // ========================================================

  else
  {

    Serial.println();


    Serial.println(
      "Wi-Fi connection FAILED!"
    );


    Serial.println(
      "Check SSID and password."
    );

  }

}


// ============================================================
// SETUP
// ============================================================

void setup()
{

  Serial.begin(
    115200
  );


  delay(
    1000
  );


  Serial.println();


  Serial.println(
    "=============================="
  );


  Serial.println(
    "5-FINGER SERVO WEB CONTROLLER"
  );


  Serial.println(
    "=============================="
  );


  // ========================================================
  // I2C
  // ========================================================

  Wire.begin(
    SDA_PIN,
    SCL_PIN
  );


  // ========================================================
  // PCA9685
  // ========================================================

  pwm.begin();


  pwm.setOscillatorFrequency(
    27000000
  );


  pwm.setPWMFreq(
    SERVO_FREQ
  );


  delay(
    100
  );


  // ========================================================
  // CENTER SERVOS
  // ========================================================

  centerAllServos();


  // ========================================================
  // WIFI
  // ========================================================

  connectToWiFi();


  // ========================================================
  // WEB ROUTES
  // ========================================================

  server.on(
    "/",
    HTTP_GET,
    handleRoot
  );


  server.on(
    "/position",
    HTTP_GET,
    handlePosition
  );


  server.on(
    "/command",
    HTTP_GET,
    handleCommand
  );


  server.onNotFound(
    handleNotFound
  );


  // ========================================================
  // START SERVER
  // ========================================================

  server.begin();


  Serial.println();


  Serial.println(
    "=============================="
  );


  Serial.println(
    "WEB SERVER STARTED"
  );


  Serial.println(
    "=============================="
  );

}


// ============================================================
// LOOP
// ============================================================

void loop()
{

  // Handle browser requests
  server.handleClient();


  // Run auto cycle without blocking
  updateAutoCycle();

}