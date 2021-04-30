import framebuf


class Icon(framebuf.FrameBuffer):

    def __init__(self, icon, width, height, mapping=framebuf.MONO_VLSB):
        self.width = width
        self.height = height
        super().__init__(icon, width, height, mapping)


class MenuItem:

    def __init__(self, name: str):
        self.parent = None
        self.is_active = False
        self.name = name
        self.decorator = ''

    def click(self):
        raise NotImplementedError()

    def get_decorator(self):
        return self.decorator


class SubMenuItem(MenuItem):

    menu = None

    def __init__(self, name):
        super().__init__(name)
        self.menu = MenuScreen(name, None)
        self.decorator = '>'

    def click(self):
        pass

    def add(self, item, parent=None) -> 'SubMenuItem':
        self.menu.add(item, parent)
        return self

    def reset(self):
        self.menu.reset()


class ToggleItem(MenuItem):

    def __init__(self, name, state_callback, change_callback, *args):
        super().__init__(name)
        self.change_callback = change_callback
        self.state_callback = state_callback
        self.args = args

    def check_status(self):
        return self.state_callback(*self.args) if len(self.args) > 0 else self.state_callback()

    def click(self):
        self.change_callback(*self.args) if len(self.args) > 0 else self.change_callback()
        return self.parent

    def get_decorator(self):
        return '[x]' if self.check_status() else '[ ]'


class SelectItem(ToggleItem):

    def __init__(self, name, status, callback, *args):
        super().__init__(name, lambda *largs: status, callback, *args)
        self.status = status

    def get_decorator(self):
        return '<<' if self.status else ''


class EnumItem(SubMenuItem):

    def __init__(self, name, items, callback=None, selected=None):
        super().__init__(name)
        self.selected = 0 if selected is None else selected
        self.items = items
        self.callback = callback
        if not isinstance(items, list):
            raise ValueError("items should be a list!")

        self._set_decorator()

    def choose(self, selection):
        self.selected = selection
        self._set_decorator()
        if callable(self.callback):
            self.callback(self._get_element()[0])

    def click(self):
        self.reset()
        for pos in range(len(self.items)):
            if isinstance(self.items[pos], dict):
                name = self.items[pos]['name']
            else:
                name = self.items[pos]
            self.add(SelectItem(name, pos == self.selected, self.choose, pos), self.parent)

        return self.menu

    def _get_element(self):
        if isinstance(self.items[self.selected], str):
            return self.items[self.selected], self.items[self.selected]

        return self.items[self.selected]['value'], self.items[self.selected]['name']

    def _set_decorator(self):
        self.decorator = self._get_element()[1]


class InfoItem(MenuItem):

    def __init__(self, name, decorator=''):
        super().__init__(name)
        self.decorator = decorator

    def click(self):
        return self.parent


class CustomItem(MenuItem):

    def __init__(self, name):
        super().__init__(name)
        self.display = None  # it is set after initialization via MenuScreen.add()

    def click(self):
        return self

    def up(self):
        # called when menu.move() is called
        pass

    def down(self):
        # called when menu.move(-1) is called
        pass

    def select(self):
        # called when menu.click() is called (on button press)
        raise NotImplementedError()

    def draw(self):
        # called when someone click on menu item
        raise NotImplementedError()


class ValueItem(CustomItem):

    def __init__(self, name, value, min_v, max_v, step, callback=None):
        super().__init__(name)
        self.value = value
        self.min_v = min_v
        self.max_v = max_v
        self.step = step
        self.callback = callback

    def draw(self):
        self.display.fill(0)
        # todo: check if rich_text exists, if not we can't use methods with align
        self.display.text(str.upper(self.name), None, 0, 1, align=self.display.TEXT_CENTER)
        self.display.hline(0, 10, self.display.width, 1)
        self.display.rich_text(str(self.value), None, 20, 1, size=5, align=self.display.TEXT_CENTER)
        self.display.show()
        if callable(self.callback):
            self.callback(self.value)

    def select(self):
        return self.parent

    def down(self):
        if self.value < self.max_v:
            self.value += self.step
        self.draw()

    def up(self):
        if self.value > self.min_v:
            self.value -= self.step
        self.draw()

    def get_decorator(self):
        return str(self.value)


class BackItem(MenuItem):

    def __init__(self, parent):
        super().__init__('< Back')
        self.parent = parent

    def click(self):
        return self.parent


class MenuScreen:

    def __init__(self, title: str, parent=None):
        self._items = []
        self.selected = 0
        self.parent = parent
        self.title = title

    def add(self, item, parent=None):
        item.parent = self if parent is None else parent
        if type(item) is SubMenuItem:
            item.menu.parent = self if parent is None else parent
        self._items.append(item)
        return self

    def reset(self):
        self._items = []

    def count(self) -> int:
        return len(self._items) + (1 if self.parent is not None else 0)

    def up(self) -> None:
        if self.selected > 0:
            self.selected = self.selected - 1

    def down(self) -> None:
        if self.selected + 1 < self.count():
            self.selected = self.selected + 1

    def get(self, position) -> MenuItem:

        if position < 0 or position + 1 > self.count():
            return None

        if position + 1 == self.count() and self.parent is not None:
            item = BackItem(self.parent)
        else:
            item = self._items[position]

        item.is_active = position == self.selected
        return item

    def select(self) -> None:

        item = self.get(self.selected)
        if type(item) is BackItem:
            self.selected = 0

        if type(item) is SubMenuItem:
            return self._items[self.selected].menu
        else:
            # do action and return current menu
            return item.click()


class Menu:

    current_screen = None

    def __init__(self, display, per_page: int = 4, line_height: int = 14, font_width: int = 8, font_height: int = 8):
        # todo: replace display and specific driver to framebuf
        self.display = display
        self.per_page = per_page
        self.line_height = line_height
        self.font_height = font_height
        self.font_width = font_width
        self.main_screen = None

    def add_screen(self, screen: MenuScreen):
        self.current_screen = screen
        if self.main_screen is None:
            self.main_screen = screen
            self._update_display(screen._items)

    def draw(self):

        if type(self.current_screen) is not MenuScreen:
            self.current_screen.draw()
            return

        self.display.fill(0)

        self.menu_header(self.current_screen.title)

        elements = self.current_screen.count()
        start = self.current_screen.selected - self.per_page + 1 if self.current_screen.selected + 1 > self.per_page else 0
        end = start + self.per_page

        menu_pos = 0
        for i in range(start, end if end < elements else elements):
            self.item_line(self.current_screen.get(i), menu_pos)
            menu_pos = menu_pos + 1

        self.display.show()

    def reset(self):
        self.current_screen = self.main_screen
        self.current_screen.selected = 0
        self.draw()

    def move(self, direction: int = 1):
        self.current_screen.up() if direction < 0 else self.current_screen.down()
        self.draw()

    def click(self):
        self.current_screen = self.current_screen.select()
        self.draw()

    def item_line(self, item: MenuItem, pos):
        menu_y_end = 12
        y = menu_y_end + (pos * self.line_height)
        v_padding = int((self.line_height - self.font_height) / 2)
        decorator_x_pos = self.display.width - (len(item.get_decorator()) * self.font_width) - 1
        background = int(item.is_active)

        self.display.fill_rect(0, y, self.display.width, self.line_height, background)
        self.display.text(item.name, 0, y + v_padding, int(not background))
        # todo: check if decorator is an icon or text
        self.display.text(item.get_decorator(), decorator_x_pos, y + v_padding, int(not background))

    def menu_header(self, text):
        x = int((self.display.width / 2) - (len(text) * self.font_width / 2))
        self.display.text(str.upper(self.current_screen.title), x, 0, 1)
        self.display.hline(0, self.font_height + 2, self.display.width, 1)

    def _update_display(self, menu_items):
        for obj in menu_items:
            if isinstance(obj, CustomItem):
                obj.display = self.display
            if isinstance(obj, SubMenuItem):
                self._update_display(obj.menu._items)
