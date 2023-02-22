from pathlib import Path
from typing import Iterable, TextIO

from PIL import Image

import settings


IMAGE_FORMAT = "PNG"
MAPPING_FORMAT = "txt"
IMAGES_FOLDER = "resources"
TUNING_FIELDS_FOLDER = f"{IMAGES_FOLDER}/tuning_fields"


class CellTypeDefiner:
    EMPTY = "empty"
    SKULL = "skull"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

    # для установления соответствия по mapping.txt
    map = {
        "e": EMPTY,
        "s": SKULL,
        "r": RED,
        "g": GREEN,
        "b": BLUE
    }

    def __init__(self):
        type_colors = self.process_tuning_fields()
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
    def get_color(cell: Image.Image) -> (int, int):
        """Получение среднего цвета (центра) ячейки."""

        compressed = cell.resize((1, 1))
        r, g, b, a = compressed.getpixel((0, 0))
        return r, g, b, a

    @classmethod
    def process_tuning_fields(cls) -> dict[str, tuple[list, list, list, list]]:
        # name: (r, g, b, a)
        # name: ([0, 1, 2, 3], (11, 12, 13, 14), (21, 22, 23, 24), (255, 255, 255, 255))
        type_colors = {
            cls.EMPTY: ([], [], [], []),
            cls.SKULL: ([], [], [], []),
            cls.RED: ([], [], [], []),
            cls.GREEN: ([], [], [], []),
            cls.BLUE: ([], [], [], [])
        }
        # todo: переделать выбор типа ячейки с проверки на вхождение в диапазон на нахождение кратчайшего расстояния

        # проход по всем полям, сохраненным в TUNING_FIELDS_FOLDER
        for field_path in get_tuning_field_folder_paths():
            # field_name = str(field_path).split('\\')[-1]
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
                cell_number = 6
                cell_width = tuning_field_image.width // cell_number
                cell_height = tuning_field_image.height // cell_number
                cell_center_offset_x = cell_width // 4
                cell_center_offset_y = cell_height // 4

                mapping = cls.cast_mapping(tuning_field_mapping)

                for h in range(6):
                    for w in range(6):
                        # нарезка поля на ячейки
                        cell_name = f"cell_{w}_{h}"
                        cell = tuning_field_image.crop(
                            (cell_width * w, cell_height * h, cell_width * (w + 1), cell_height * (h + 1))
                        )

                        # вырезка центра ячейки для лучшего определения цвета (фон поля мешает)
                        cell_center = cell.crop(
                            (
                                cell_center_offset_y,
                                cell_center_offset_x,
                                cell_width - cell_center_offset_x,
                                cell_height - cell_center_offset_y
                            )
                        )

                        # сохранение изображений ячеек при настройке распознавателя
                        if settings.SAVE_TUNING_FIELD_IMAGE_CELLS:
                            cell.save(f"{cells_folder}/{cell_name}.{IMAGE_FORMAT}")
                            cell_center.save(f"{cell_centers_folder}/{cell_name}.{IMAGE_FORMAT}")

                        # обновление минимальных и максимальных значений цветов
                        cell_type = cls.map[mapping[h][w]]
                        type_color = type_colors[cell_type]
                        cell_color = cls.get_color(cell_center)
                        # r, g, b, a
                        for component_number in range(4):
                            type_color[component_number].append(cell_color[component_number])
        return type_colors


def get_tuning_field_folder_paths() -> Iterable[Path]:
    return Path(TUNING_FIELDS_FOLDER).rglob(f"field_*")


if __name__ == "__main__":
    cell_type_definer = CellTypeDefiner()
    print_type_colors = True
    if print_type_colors:
        print("type:\tr\tg\tb\ta")
        for i in cell_type_definer.type_colors:
            color_string = '\t'.join(map(str, cell_type_definer.type_colors[i]))
            print(f"{i}:\t{color_string}")
