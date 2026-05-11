/*
 * GhostStack: Optical Disruption Module
 * File: optical_strobe.ino
 * 
 * Description:
 * This sketch drives a high-power IR LED array via a MOSFET.
 * It uses a randomized strobe frequency to disrupt rolling shutters.
 * Now supports automated Serial triggering from GhostStack-CTL.
 */

#define STROBE_PIN 4       // GPIO pin connected to MOSFET Gate
#define MIN_FREQ 50        // Minimum frequency in Hz
#define MAX_FREQ 2000      // Maximum frequency in Hz
#define DUTY_CYCLE 50      // 50% duty cycle

bool is_strobing = false;

void setup() {
  Serial.begin(115200);
  pinMode(STROBE_PIN, OUTPUT);
  digitalWrite(STROBE_PIN, LOW);
  
  // Initialize random seed
  randomSeed(analogRead(0));
  
  Serial.println("[!] GhostStack Optical Module Initialized");
  Serial.println("[*] Awaiting Serial Commands (1 = ON, 0 = OFF)");
}

void loop() {
  // Check for incoming Serial commands from Master Controller
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '1') {
      is_strobing = true;
      Serial.println("[+] STROBE ENGAGED");
    } else if (cmd == '0') {
      is_strobing = false;
      digitalWrite(STROBE_PIN, LOW); // Ensure LEDs are off
      Serial.println("[-] STROBE DISENGAGED");
    }
  }

  // Execute strobe logic if active
  if (is_strobing) {
    int currentFreq = random(MIN_FREQ, MAX_FREQ);
    long periodMicros = 1000000 / currentFreq;
    long onTime = (periodMicros * DUTY_CYCLE) / 100;
    long offTime = periodMicros - onTime;

    long burstDuration = millis() + random(50, 200);
    
    while(millis() < burstDuration && !Serial.available()) {
      digitalWrite(STROBE_PIN, HIGH);
      delayMicroseconds(onTime);
      digitalWrite(STROBE_PIN, LOW);
      delayMicroseconds(offTime);
    }
  }
}
