import enum
from pathlib import Path
from typing import Iterable, TextIO

from PIL import Image

import settings


IMAGE_FORMAT = "PNG"
MAPPING_FORMAT = "txt"
IMAGES_FOLDER = "resources"
TUNING_FIELDS_FOLDER = f"{IMAGES_FOLDER}/tuning_fields"
TEST_FIELDS_FOLDER = f"{IMAGES_FOLDER}/test_fields"

# количество ячеек в ширину и высоту
CELL_NUMBER = 6

Color = tuple[int, int, int, int]


class CellType(enum.Enum):
    EMPTY = "empty"
    SKULL = "skull"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

    @staticmethod
    def map(character: str) -> "CellType":
        mapping = {
            "e": CellType.EMPTY,
            "s": CellType.SKULL,
            "r": CellType.RED,
            "g": CellType.GREEN,
            "b": CellType.BLUE
        }
        return mapping[character]

    @staticmethod
    def reverse_map(character: "CellType") -> str:
        reverse_mapping = {
            CellType.EMPTY: "e",
            CellType.SKULL: "s",
            CellType.RED: "r",
            CellType.GREEN: "g",
            CellType.BLUE: "b"
        }
        return reverse_mapping[character]


class Cell:
    # level - уровень камня/ячейки [1:5]
    def __init__(self, cell_type: CellType, level: int, image: Image.Image):
        self.type = cell_type
        self.level = level
        self.image = image

    def __str__(self):
        return self.type.reverse_map(self.type)


class Field:
    def __init__(self, cells: list[list[Cell]]):
        self.cells = cells

    def __str__(self):
        string = '\n'.join([' '.join(map(str, line)).strip() for line in self.cells]).strip()
        return string


class FieldImageProcessor:
    type_colors: dict[CellType, Color]

    def __init__(self):
        type_colors = self.process_tuning_field_images()
        # name: (r, g, b, a)
        # name: средневзвешенный цвет
        self.type_colors = {
            cell_type: tuple(sum(component) // len(component) for component in type_color)
            for cell_type, type_color in type_colors.items()
        }

    @staticmethod
    def cast_mapping(mapping: TextIO) -> list[list[str]]:
        new_mapping = [x.split() for x in mapping]
        return new_mapping

    @staticmethod
    def get_color(cell_image: Image.Image) -> (int, int):
        """Получение среднего цвета (центра) ячейки."""

        compressed = cell_image.resize((1, 1))
        r, g, b, a = compressed.getpixel((0, 0))
        return r, g, b, a

    @classmethod
    def process_tuning_field_images(cls) -> dict[CellType, tuple[list, list, list, list]]:
        """Настройка для распознавания типов ячеек."""

        # name: (r, g, b, a)
        # name: ([0, 1, 2, 3], (11, 12, 13, 14), (21, 22, 23, 24), (255, 255, 255, 255))
        type_colors = {
            CellType.EMPTY: ([], [], [], []),
            CellType.SKULL: ([], [], [], []),
            CellType.RED: ([], [], [], []),
            CellType.GREEN: ([], [], [], []),
            CellType.BLUE: ([], [], [], [])
        }

        # проход по всем полям, сохраненным в TUNING_FIELDS_FOLDER
        for field_path in get_tuning_field_folder_paths():
            field_image_path = f"{field_path}/image.{IMAGE_FORMAT}"
            field_mapping_path = f"{field_path}/mapping.{MAPPING_FORMAT}"
            with Image.open(field_image_path) as tuning_field_image, open(field_mapping_path) as tuning_field_mapping:
                # создание папок для хранения изображений ячеек и центров ячеек поля
                if settings.SAVE_TUNING_FIELD_IMAGE_CELLS:
                    cells_folder = f"{field_path}/cells"
                    cell_centers_folder = f"{field_path}/cell_centers"
                    Path(cells_folder).mkdir(parents = True, exist_ok = True)
                    Path(cell_centers_folder).mkdir(parents = True, exist_ok = True)

                tuning_field_image: Image.Image
                cell_width = tuning_field_image.width // CELL_NUMBER
                cell_height = tuning_field_image.height // CELL_NUMBER
                cell_center_offset_x = cell_width // 4
                cell_center_offset_y = cell_height // 4

                mapping = cls.cast_mapping(tuning_field_mapping)

                for h in range(6):
                    for w in range(6):
                        # нарезка поля на ячейки
                        cell_name = f"cell_{w}_{h}"
                        cell_image = tuning_field_image.crop(
                            (cell_width * w, cell_height * h, cell_width * (w + 1), cell_height * (h + 1))
                        )

                        # вырезка центра ячейки для лучшего определения цвета (фон поля мешает)
                        cell_center_image = cell_image.crop(
                            (
                                cell_center_offset_y,
                                cell_center_offset_x,
                                cell_width - cell_center_offset_x,
                                cell_height - cell_center_offset_y
                            )
                        )

                        # сохранение изображений ячеек при настройке распознавателя
                        if settings.SAVE_TUNING_FIELD_IMAGE_CELLS:
                            cell_image.save(f"{cells_folder}/{cell_name}.{IMAGE_FORMAT}")
                            cell_center_image.save(f"{cell_centers_folder}/{cell_name}.{IMAGE_FORMAT}")

                        # обновление минимальных и максимальных значений цветов
                        cell_type = CellType.map(mapping[h][w])
                        type_color = type_colors[cell_type]
                        cell_color = cls.get_color(cell_center_image)
                        # r, g, b, a
                        for component_number in range(4):
                            type_color[component_number].append(cell_color[component_number])
        return type_colors

    def test_field_processing(self):
        # проход по всем полям, сохраненным в TEST_FIELDS_FOLDER
        for field_path in get_test_field_folder_paths():
            field_image_path = f"{field_path}/image.{IMAGE_FORMAT}"
            field_mapping_path = f"{field_path}/mapping.{MAPPING_FORMAT}"
            with Image.open(field_image_path) as test_field_image, open(field_mapping_path) as test_field_mapping:
                field = self.process_field_image(test_field_image)
                # todo: написать сравнение mapping.txt и полученного поля

    def process_field_image(self, field_image: Image.Image) -> Field:
        field_image: Image.Image
        cell_width = field_image.width // CELL_NUMBER
        cell_height = field_image.height // CELL_NUMBER

        cells = [[] for _ in range(CELL_NUMBER)]

        for h in range(6):
            for w in range(6):
                # нарезка поля на ячейки
                cell_image = field_image.crop(
                    (cell_width * w, cell_height * h, cell_width * (w + 1), cell_height * (h + 1))
                )
                cells[h].append(self.process_cell_image(cell_image))
        return Field(cells)

    def calculate_color_distances(self, cell_color: Color) -> dict[CellType, float]:
        distances = {cell_type: (sum((type_color[number] - cell_color[number])**2 for number in range(4)))**(1 / 2)
                     for cell_type, type_color in self.type_colors.items()}
        return distances

    def define_cell_type(self, cell_image: Image.Image) -> CellType:
        cell_color = self.get_color(cell_image)
        distances = self.calculate_color_distances(cell_color)
        cell_type = min(distances, key = distances.get)
        return cell_type

    def process_cell_image(self, cell_image: Image.Image) -> Cell:
        cell_center_offset_x = cell_image.width // 4
        cell_center_offset_y = cell_image.height // 4
        # вырезка центра ячейки для лучшего определения цвета (фон поля мешает)
        cell_center = cell_image.crop(
            (
                cell_center_offset_y,
                cell_center_offset_x,
                cell_image.width - cell_center_offset_x,
                cell_image.height - cell_center_offset_y
            )
        )
        cell_type = self.define_cell_type(cell_center)
        # todo: реализовать определение уровня камня
        cell_level = 1
        cell = Cell(cell_type, cell_level, cell_image)
        return cell


def get_test_field_folder_paths() -> Iterable[Path]:
    return Path(TEST_FIELDS_FOLDER).rglob(f"field_*")


def get_tuning_field_folder_paths() -> Iterable[Path]:
    return Path(TUNING_FIELDS_FOLDER).rglob(f"field_*")


if __name__ == "__main__":
    field_image_processor = FieldImageProcessor()
    print_type_colors = True
    if print_type_colors:
        print("type:\tr\tg\tb\ta")
        for i in field_image_processor.type_colors:
            color_string = '\t'.join(map(str, field_image_processor.type_colors[i]))
            print(f"{i.value}:\t{color_string}")

    field_image_processor.test_field_processing()
