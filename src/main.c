#include <stdio.h>
#include "raylib.h"

#define T_RED (Color){ 230, 41, 55, 127 }
#define T_BLUE (Color){ 0, 121, 241, 127 }

typedef struct {
  int top;
  int bottom;
  int left;
  int right;
  Color color;
} ExtendedEdges;


typedef struct {
  int x;
  int y;
  int w;
  int h;
  ExtendedEdges edges;
  Color color;
} Button;

Button new_button(int x, int y, int w, int h, ExtendedEdges edges, Color color){
  Button button = { x, y, w, h, edges, color };
  return button;
}

void DrawButton(Button button){
  DrawRectangle(
    button.x - button.edges.left,
    button.y - button.edges.top,
    button.edges.left + button.w + button.edges.right,
    button.edges.top + button.h + button.edges.bottom,
    button.edges.color
  );
  DrawRectangle(button.x, button.y, button.w, button.h, button.color);
}

int main(void){
  InitWindow(800, 450, "raylib [core] example - basic window");
  bool moving = 0;
  Vector2 tmp;
  Button buttons[20];
  int but = 1;

  ExtendedEdges edges = { 10, 10, 10, 10, T_RED};
  Button button = new_button(100, 100, 100, 100, edges, T_BLUE);

  buttons[0] = button;

  SetConfigFlags(FLAG_VSYNC_HINT);
  SetTargetFPS(30);

  while (!WindowShouldClose()){
    if (IsKeyPressed(KEY_L)) moving = !moving;
    if (moving){
      Vector2 tmp = GetMousePosition();
      buttons[but-1].x = (int)tmp.x - (int)((float)buttons[but-1].w / 2.0f);
      buttons[but-1].y = (int)tmp.y - (int)((float)buttons[but-1].h / 2.0f);
    }

    if (IsKeyPressed(KEY_W)) {
      TraceLog(LOG_INFO, "button: %i %i %i %i", buttons[but-1].x, buttons[but-1].y, buttons[but-1].w, buttons[but-1].h);
    }
    if (IsKeyPressed(KEY_N)) {
      TraceLog(LOG_INFO, "new button %i", but);
      Button button = new_button(100, 100, 100, 100, (ExtendedEdges){ 10, 10, 10, 10, T_RED}, T_BLUE);
      buttons[but] = button;
      but++;
    }
    if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)){
      tmp = GetMousePosition();
      TraceLog(LOG_INFO, "%i %i", (int)tmp.x, (int)tmp.y);
    }
    if (IsMouseButtonReleased(MOUSE_BUTTON_LEFT)){
      tmp = GetMousePosition();
      TraceLog(LOG_INFO, "%i %i", (int)tmp.x, (int)tmp.y);
    }
      
    if (IsKeyDown(KEY_LEFT)) {
      if (IsKeyDown(KEY_LEFT_SHIFT) | IsKeyDown(KEY_RIGHT_SHIFT)){
        buttons[but-1].w--;
      } else {
        buttons[but-1].w++;
      }
    }
    if (IsKeyDown(KEY_RIGHT)) {
      if (IsKeyDown(KEY_LEFT_SHIFT) | IsKeyDown(KEY_RIGHT_SHIFT)){
        buttons[but-1].x--;
      } else {
        buttons[but-1].x++;
      }
    }
    if (IsKeyDown(KEY_UP)) {
      if (IsKeyDown(KEY_LEFT_SHIFT) | IsKeyDown(KEY_RIGHT_SHIFT)){
        buttons[but-1].h--;
      } else {
        buttons[but-1].h++;
      }
    }
    if (IsKeyDown(KEY_DOWN)) {
      if (IsKeyDown(KEY_LEFT_SHIFT) | IsKeyDown(KEY_RIGHT_SHIFT)){
        buttons[but-1].y--;
      } else {
        buttons[but-1].y++;
      }
    }

    BeginDrawing();
    for (int i = 0; i < but + 1; i++){
      DrawButton(buttons[i]);
    }

    ClearBackground(RAYWHITE);
    //DrawRectangle(x-30, y-30, w+60, h+60, RED);
    //DrawRectangle(x, y, w, h, BLUE);
    DrawText("Congrats! You made it!", 190, 200, 20, LIGHTGRAY);

    EndDrawing();
  }

  CloseWindow();

  return 0;
}
