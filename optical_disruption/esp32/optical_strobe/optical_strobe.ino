/*
 * GhostStack: Optical Disruption Module
 * File: optical_strobe.ino
 * 
 * Description:
 * This sketch drives a high-power IR LED array via a MOSFET.
 * It uses a randomized strobe frequency to:
 * 1. Desynchronize rolling-shutter cameras (creating "light banding").
 * 2. Overload/Confuse LiDAR mapping sensors by introducing high-intensity 
 *    asynchronous pulses.
 * 
 * Hardware:
 * - ESP32 (S3 or standard)
 * - N-Channel MOSFET (e.g., IRLZ44N)
 * - High-power IR LED Array (850nm or 940nm)
 */

#define STROBE_PIN 4       // GPIO pin connected to MOSFET Gate
#define MIN_FREQ 50        // Minimum frequency in Hz
#define MAX_FREQ 2000      // Maximum frequency in Hz
#define DUTY_CYCLE 50      // 50% duty cycle

void setup() {
  Serial.begin(115200);
  pinMode(STROBE_PIN, OUTPUT);
  
  // Initialize random seed from noise on an unconnected analog pin
  randomSeed(analogRead(0));
  
  Serial.println("[!] GhostStack Optical Module Initialized");
  Serial.println("[*] Target: Rolling Shutter & LiDAR Disruption");
}

void loop() {
  // Randomize the frequency to prevent the target system's 
  // auto-exposure/filter logic from adapting.
  int currentFreq = random(MIN_FREQ, MAX_FREQ);
  
  // Calculate period in microseconds
  long periodMicros = 1000000 / currentFreq;
  long onTime = (periodMicros * DUTY_CYCLE) / 100;
  long offTime = periodMicros - onTime;

  // Execute strobe for a random duration (50ms to 200ms) before changing frequency
  long burstDuration = millis() + random(50, 200);
  
  while(millis() < burstDuration) {
    digitalWrite(STROBE_PIN, HIGH);
    delayMicroseconds(onTime);
    digitalWrite(STROBE_PIN, LOW);
    delayMicroseconds(offTime);
  }
  
  // Log frequency shift for research debugging
  // Serial.print("[+] Shifted to Freq: ");
  // Serial.print(currentFreq);
  // Serial.println(" Hz");
}
