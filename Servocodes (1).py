from flask import Flask, jsonify, render_template_string
from adafruit_servokit import ServoKit
import time
import busio
from board import SCL, SDA

app = Flask(__name__)

# ---------------------------
# Servo INIT
# ---------------------------
i2c = busio.I2C(SCL, SDA)
kit = ServoKit(channels=16, i2c=i2c, address=0x40)

# ---------------------------
# Robot Actions
# ---------------------------

def stand():
    kit.servo[3].angle = 0
    kit.servo[7].angle = 180
    stand1()
    kit.servo[10].angle = 0
    time.sleep(0.1)
    kit.servo[14].angle = 180
    
    


    kit.servo[1].angle = 90
    time.sleep(0.1)
    kit.servo[5].angle = 90
    time.sleep(0.1)
    kit.servo[9].angle = 90
    time.sleep(0.1)
    kit.servo[13].angle = 90


    kit.servo[2].angle = 90
    time.sleep(0.1)
    kit.servo[6].angle = 90
    time.sleep(0.1)
    kit.servo[10].angle = 90
    time.sleep(0.1)
    kit.servo[14].angle = 90


    kit.servo[11].angle = 30
    time.sleep(0.1)
    kit.servo[15].angle = 150
    time.sleep(0.1)
    kit.servo[3].angle = 150
    time.sleep(0.1)
    kit.servo[7].angle = 30
    time.sleep(0.3)

    time.sleep(5)
    

def stand1(): # for standing up pre prossing
    kit.servo[15].angle = 0
    kit.servo[14].angle = 180
    kit.servo[11].angle = 180
    kit.servo[10].angle = 0
    time.sleep(0.5)
    kit.servo[15].angle = 90
    kit.servo[11].angle = 90
    time.sleep(0.5)
    kit.servo[14].angle = 130
    kit.servo[15].angle = 90
    kit.servo[10].angle = 50
    kit.servo[11].angle = 90
    time.sleep(0.5)
    
    
def sit():
    sit1()

    kit.servo[1].angle = 90
    time.sleep(0.1)
    kit.servo[5].angle = 90
    time.sleep(0.1)
    kit.servo[9].angle = 90
    time.sleep(0.1)
    kit.servo[13].angle = 90


    kit.servo[2].angle = 90
    time.sleep(0.1)
    kit.servo[6].angle = 90
    time.sleep(0.1)
    kit.servo[10].angle = 90
    time.sleep(0.1)
    kit.servo[14].angle = 90


    kit.servo[3].angle = 150
    time.sleep(0.1)
    kit.servo[7].angle = 30
    time.sleep(0.3)
    kit.servo[11].angle = 130
    time.sleep(0.1)
    kit.servo[15].angle = 60
    time.sleep(1)


    kit.servo[3].angle = 105
    time.sleep(0.1)
    kit.servo[7].angle = 60
    time.sleep(0.3)

def sit1():
    kit.servo[14].angle = 180
    kit.servo[10].angle = 0
    time.sleep(1)
    kit.servo[15].angle = 0
    kit.servo[11].angle = 180
    time.sleep(1)
    kit.servo[14].angle = 90
    kit.servo[10].angle = 90
    

def full_Sit():
    #sit()
    kit.servo[3].angle = 0
    kit.servo[7].angle = 180
    kit.servo[2].angle = 120
    kit.servo[6].angle = 50
    kit.servo[10].angle = 60
    kit.servo[14].angle = 120
    kit.servo[11].angle = 180
    kit.servo[15].angle = 0


# ---------------------------
# Beautiful Frontend UI
# ---------------------------

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Humanoid Control Panel</title>

<style>
    body {
        background: linear-gradient(135deg, #0a0f24, #1b264b);
        color: #fff;
        font-family: 'Poppins', sans-serif;
        text-align: center;
        padding-top: 80px;
    }
    h1 {
        font-size: 40px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    p { opacity: 0.8; }

    .btn {
        padding: 18px 40px;
        margin: 20px;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        font-size: 22px;
        font-weight: 600;
        color: white;
        transition: 0.2s;
    }

    .stand {
        background: #2ecc71;
        box-shadow: 0px 0px 20px #2ecc71a0;
    }
    .stand:hover { transform: scale(1.08); }

    .sit {
        background: #C49102;
        box-shadow: 0px 0px 20px #e74c3ca0;
    }

    .full_sit {
        background: #e74c3c;
        box-shadow: 0px 0px 20px #e74c3ca0;
    }
    .sit:hover { transform: scale(1.08); }

    #status {
        margin-top: 40px;
        font-size: 22px;
        opacity: 0.9;
    }

</style>

</head>
<body>

<h1>Humanoid Control Panel</h1>
<p>Take command. Rule your robot.</p>

<button class="btn stand" onclick="callAPI('/stand')">Stand</button>
<button class="btn sit" onclick="callAPI('/sit')">Sit</button>
<button class="btn full_sit" onclick="callAPI('/full_sit')">Full Sit</button>

<div id="status"></div>

<script>
function callAPI(route) {
    document.getElementById("status").innerHTML = "Executing...";
    fetch(route)
        .then(res => res.json())
        .then(data => {
            document.getElementById("status").innerHTML =
                "Action: " + data.action + " ✓";
        })
        .catch(err => {
            document.getElementById("status").innerHTML =
                "Error: " + err;
        });
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/stand")
def stand_route():
    try:
        stand()
        return jsonify({"action": "stand"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/sit")
def sit_route():
    try:
        sit()
        return jsonify({"action": "sit"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/full_sit")
def full_sit_route():
    try:
        full_Sit()
        return jsonify({"action": "full_sit"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
