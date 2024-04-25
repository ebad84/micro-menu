class SimpleMenu:
    def __init__(self, display, title: str = None, per_page: int = 4, line_height: int = 14, font_width: int = 8, font_height: int = 8):
        self.display = display
        self.per_page = per_page
        self.line_height = line_height
        self.font_height = font_height
        self.font_width = font_width
        self.title = '' if title == None else title
        self.items = []
        self.selected = 0
        
    def add_item(self, name:str, value = None):
        value = name if value == None else value
        self.items.append([name, value])# [name, value]
    
    def move_up(self):
        self.selected -= 1
        if self.selected < 0:# don't let him get up more
            self.selected = len(self.items)-1
            
    def move_down(self):
        self.selected += 1
        if self.selected > len(self.items)-1:# don't let him get down more
            self.selected = 0
            
    def select(self):
        return self.items[self.selected][1] # return the NOW SELECTED VALUE
    
    def update_display(self):
        display.fill(0)
        text = self.title
        if text != '':
            x = int((self.display.width / 2) - (len(text) * self.font_width / 2))
            self.display.text(str.upper(text), x, 0, 1)
            self.display.hline(0, self.font_height + 2, self.display.width, 1)
        items_list = self.items[self.selected:]
        for pos in range(0, len(items_list)):
            item = items_list[pos]
            menu_y_end = 12
            y = menu_y_end + (pos * self.line_height)
            v_padding = int((self.line_height - self.font_height) / 2)
            background = 0 if pos != 0 else 1

            self.display.fill_rect(0, y, self.display.width, self.line_height, background)
            self.display.text(item[0], 0, y + v_padding, int(not background))
            x_pos = display.width - (len('') * self.font_width) - 1
            self.display.text('', x_pos, y + v_padding, int(not background))
        display.show()
            
    

from machine import Pin, I2C
import ssd1306

i2c = I2C(sda=Pin(0), scl=Pin(5))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

mymenu = SimpleMenu(display, "this is my menu!")
for i in range(1,10):
    mymenu.add_item("item #" + str(i)) # add menu items
mymenu.update_display() # update/show all the changes
while True:
    data = input(">")
    if data == "u":
        mymenu.move_up()
    if data == "d":
        mymenu.move_down()
    if data == "s":
        print(mymenu.select())
    if data == "q":
        break
    mymenu.update_display()
    
    
