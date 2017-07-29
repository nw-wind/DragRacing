#include "SmartDelay.h"
#include "SmartButton.h"

template<class T> inline Print &operator <<(Print &obj, T arg) {
  obj.print(arg);
  return obj;
}
#define endl ("\n")

#define KNOB  9

struct player {
  volatile unsigned long d; // distanse (mm)
  volatile unsigned long c; // rotation counter
  unsigned long t; // время дистанции ms
} pl[2];
byte pp[2] = {2, 3};
#define PLAYERS (sizeof(pp)/sizeof(byte))

byte start = 0;

const unsigned long circle = (unsigned long)(3.14f * 300.0f); // длина окружности барабана mm
const unsigned long distance = 4UL * 1000UL; //402UL * 1000UL; // дистанция пробега mm
const unsigned long rotations = distance / circle; // оборотов до финиша

unsigned long idleTime = 0;

SmartDelay disp(250000UL);

class Baton : public SmartButton {
  public:
    Baton(int p) : SmartButton(p) {}
    void onClick() {
      if (!start) {
        start = 1;
        idleTime = millis();
        for (int i = 0; i < PLAYERS; i++) {
          pl[i].d = 0L;
          pl[i].c = 0L;
          pl[0].t = 0L;
        }
        Serial.println("START");
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
  attachInterrupt(digitalPinToInterrupt(pp[0]), getInt0, RISING);
  attachInterrupt(digitalPinToInterrupt(pp[1]), getInt1, RISING);
  Serial.println("READY");
  //Serial << circle << " " << distance << " " << rotations << endl;
}

void loop() {
  bt.run();
  if (start) {
    // Считаем время и расстояние
    for (int i = 0; i < PLAYERS; i++) {
      pl[i].d = pl[i].c * circle;
      if (pl[i].c <= rotations) pl[i].t = millis() - idleTime;
    }
    // Выводим в компорт
    if (disp.Now()) {
      for (int i = 0; i < PLAYERS; i++) {
        if (pl[i].c > rotations) {
          Serial << pl[i].t << " FINISH ";
        } else
          Serial << pl[i].t << " " << pl[i].d << " ";
      }
      Serial.println();
    }
    // Если оба финишировали, заканчиваем.
    if (pl[0].c > rotations && pl[1].c > rotations) {
      start = 0;
      for (int i = 0; i < PLAYERS; i++) {
        Serial << pl[i].t << " FINISH ";
      }
      Serial.println();

    }
  }
}
