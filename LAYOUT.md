# `Screen` Edge Cases
* Handle `screens` section of `info.json`
* DS bottom screen input handling will be in `'items'`
* Output screens will be under its own `'screens'`
  * `inputFrame` is for what the emulator core outputs
  * `outputFrame` is for what the user sees as output
    * Use `outputFrame` to scale `inputFrame`
  * Sega Genesis does not have `inputFrame` because of 
  massive variations in emulator outputs, only use `outputFrame` for these
  * DS outputs top and bottom screens together stacked on top of each other,
  meaning you should split the screen's height in half if you want to place 
  it elsewhere on the screen of your skin.
    * Introduce this concept to users, showing a preview of the content they
    will see when splitting, placing, etc

# Canvas
* Hold `Region` objects in a list for easy grabbing
* Hold currently selected `Region`
* Hold current representation configuration
  * Default Extended edges
  * Mapping Size
  * Assets
* Export current configuration from `Region`'s and self 
  * Each `Region`'s configuration, and export it to `items` list
  * Each `Screen`'s configuration, and export it to `screens` list

# Region
* `Extended` / `Touch` rectangle
  * Hold the image object representing touch rectangle
  * Hold the configuration it is representing
* Handle movement / resizing of extended / touch rectangles
* Handle configuration updates
  * `item`
    * `frame`
      * x
      * y
      * width
      * height
    * `extendedEdges`
      * Either be the default for current representation, or defined here
      * top
      * bottom
      * right
      * left
        * If any aren't defined, use `Canvas` default for empty value
        * If desired EE is 0, define as 0 ex. `"top": 0`
