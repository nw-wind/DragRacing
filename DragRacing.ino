#include "SmartDelay.h"
#include "SmartButton.h"

// светофор!! внешнее управление!! 1s

template<class T> inline Print &operator <<(Print &obj, T arg) {
  obj.print(arg);
  return obj;
}
#define endl ("\n")

#define KNOB  9
#define INDICATOR 13

struct player {
  volatile unsigned long d; // distanse (mm)
  volatile unsigned long c; // rotation counter
  unsigned long t; // время дистанции ms
} pl[2];
struct player op[2]; // for calculations out of interrupt.
byte pp[2] = {2, 3};
#define PLAYERS (sizeof(pp)/sizeof(byte))

byte start = 0;

const unsigned long circle = (unsigned long)(3.1416926f * 108.0f); // длина окружности барабана mm
const unsigned long distance = 402UL * 1000UL; //402UL * 1000UL; // дистанция пробега mm
const unsigned long rotations = distance / circle; // оборотов до финиша

unsigned long idleTime = 0;

SmartDelay disp(250*1000UL);

class Baton : public SmartButton {
  public:
    Baton(int p) : SmartButton(p) {}
    void onClick() {
      if (start) {
        start = 0;
        Serial.println("STOP");
        digitalWrite(INDICATOR,LOW);
      } else {
        start = 1;
        idleTime = millis();
        for (int i = 0; i < PLAYERS; i++) {
          pl[i].d = 0L;
          pl[i].c = 0L;
          pl[0].t = 0L;
        }
        Serial.println("START");
        digitalWrite(INDICATOR,HIGH);
      }
    }
};
Baton bt(KNOB);

void getInt0() {
  pl[0].c++;
}

void getInt1() {
  pl[1].c++;
}

void setup() {
  Serial.begin(115200);
  pinMode(KNOB, INPUT_PULLUP);
  for (int i = 0; i < PLAYERS; i++) {
    pinMode(pp[i], INPUT_PULLUP);
  }
  pinMode(INDICATOR,OUTPUT);
  attachInterrupt(digitalPinToInterrupt(pp[0]), getInt0, RISING);
  attachInterrupt(digitalPinToInterrupt(pp[1]), getInt1, RISING);
  Serial.println("READY");
  //Serial << circle << " " << distance << " " << rotations << endl;
}

void loop() {
  bt.run();
  if (start) {
    // Считаем время и расстояние
    unsigned long sc[2]; // saved counters
    for (int i = 0; i < PLAYERS; i++) {
      sc[i]=pl[i].c;
      pl[i].d = sc[i] * circle;
      if (sc[i] <= rotations) pl[i].t = millis() - idleTime;
    }
    // Выводим в компорт
    if (disp.Now()) {
      for (int i = 0; i < PLAYERS; i++) {
        if (sc[i] > rotations) {
          Serial << pl[i].t << " FINISH ";
        } else
          Serial << pl[i].t << " " << pl[i].d / 1000UL << " ";
      }
      Serial.println();
    }
    // Если оба финишировали, заканчиваем.
    if (sc[0] > rotations && sc[1] > rotations) {
      start = 0;
      for (int i = 0; i < PLAYERS; i++) {
        Serial << pl[i].t << " FINISH ";
      }
      Serial.println();
      Serial.println("STOP");
    }
  }
}
