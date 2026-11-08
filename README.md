# Обработка результатов моделирования

Независимые процедуры анализа двух гидроприводов Lift и Tilt.
Имена процедур: `plot_<величина>_<параметр или вид графика>.py` для графиков
и `export_<результат>.py` для экспорта таблиц, в стиле `snake_case`.
Парные процедуры для исходных данных и CSV имеют одинаковые имена в разных папках.
Текущий источник — `commitable_data/`, выбранный в `utils/paths.py` (`DATA_DIR`).
Полные наборы `rawdata/` и `refpress_data/` хранятся локально и исключены из Git.
Таблицы результатов сохраняются в `csv_files/`, рисунки — в `figures/`.
Исходные данные при обработке не перезаписываются.

Запускать из корня проекта с установленными NumPy, pandas, Matplotlib и tqdm:

```shell
python main.py
python -m procedures_raw.export_hydraulic_energy_balance
python -m procedures_raw.export_hydraulic_energy_balance_by_motion
python -m procedures_raw.export_model_validation_metrics
python -m procedures_raw.export_boom_angle_error_metrics
python -m procedures_raw.plot_valve_supply_flows
python -m procedures_raw.plot_boom_angle_scenarios
python -m procedures_raw.export_lightweighting_flow_power_correlations
python -m procedures_raw.export_lightweighting_energy_attribution
python -m procedures_raw.export_valve_flow_energy_by_motion
python -m procedures_raw.plot_pump_energy_change_by_motion
python -m procedures_csv.plot_pump_energy_change_heatmap
```

`main.py` сравнивает мощность насоса для случаев `(0, 400, 30)` и `(30, 400, 30)`
из текущего набора после 2,4 с. Параметры остальных процедур сохранены: перед
запуском нужно согласовать `case_set` / `l_set`, `p_set`, `r_set` с доступными файлами.
Масштаб кодов давления `R` автоматически не меняется.
PID-процедуры требуют `target_u/`; графики энергетических балансов — дополнительный экспорт
угловых скоростей шарниров (полный набор может находиться в `rawdata_powerbalance/`).

`export_hydraulic_energy_balance.py` обрабатывает все TXT из `commitable_data/`
и создаёт `csv_files/hydraulic_energy_balance.csv`: облегчение (%), `rfp` (R из имени
без пересчёта), нагрузка (кг), энергия насоса и энергии/доли Lift, Tilt, накопления,
дросселирования и невязки. Энергии в кДж, доли от насоса в %, со знаком.
Используются весь записанный интервал и фильтрация гидравлического баланса (20/100 отсчётов).

`export_hydraulic_energy_balance_by_motion.py` создаёт отдельный
`csv_files/hydraulic_energy_balance_by_motion.csv`: четыре строки на каждый датасет,
с номером движения и границами времени. Интервалы: 1 — 2.5–8.5 с, 2 — 8.5–15 с,
3 — 15–21 с, 4 — от 21 с до конца записи. Мощности фильтруются на полной записи;
на границах интегрирования применяется линейная интерполяция. Доли рассчитаны
от энергии насоса соответствующего движения. Участок до 2.5 с не включается.

`export_model_validation_metrics.py` создаёт `csv_files/model_validation_metrics.csv`
с RMSE, максимальной абсолютной ошибкой и bias (`sim - exp`) для двух углов (rad)
и четырёх давлений (bar) из `plot_model_vs_experiment.py`. Начало сравнения — точно
`t = 2.5 с`; сохранена подготовка углов с шагом 0.001 с. Сравнение идёт только
в общем диапазоне исходных данных (2.5–29.952 с), с линейной интерполяцией
на объединённую сетку времени и временными весами (интегрирование трапециями).

`export_boom_angle_error_metrics.py` создаёт `csv_files/boom_angle_error_metrics.csv`
для всех сценариев `commitable_data/`: облегчение, `rfp`, нагрузка и отдельно для
Lift/Tilt три показателя ошибки `e = theta_sim - theta_ref`: RMSE с временными весами,
максимум `abs(e)` и средняя знаковая ошибка (bias) `integral(e dt) / T`.
Все показатели в радианах; это характеристики ошибки, а не самого угла.
Эталон — `target_thetas/`, подготовка с шагом 0.001 с, интервал 2.5–29.952 с.

`plot_boom_angle_scenarios.py` и `plot_valve_supply_flows.py` сохраняют каждый график
Lift/Tilt в отдельный PDF/PNG без заголовка, а общую легенду — в отдельный файл.
Случаи: 0%/30% × 10/400 кг при 30 bar; обозначения `L`, `m_pld`, `delta p_LS`.
В легенде пары 0%/30% стоят столбцами, референс справа. Референтные углы из
`target_thetas`, расходы из `validatio.txt` — пунктиром. На расходах и давлениях
из `plot_model_vs_experiment.py` добавлен фон с разделителями движений.
Графики начинаются с 0 с, граница 2.5 с отмечается линией;
расчётные окна метрик и энергетических таблиц сохраняются от 2.5 с.
Обе процедуры построения самостоятельны: настройки и последовательные блоки
`READING`, `PROCESSING`, `PLOTTING`, `LEGEND`, `SAVING` находятся в самом файле.
`export_lightweighting_flow_power_correlations.py` создаёт независимую таблицу
`csv_files/lightweighting_flow_power_correlations.csv`: для 20 пар 0%/30% и четырёх
движений коррелируются изменения мощности и трёх расходов. Мощность обрабатывается
точно как в `plot_pump_power_change.py` (окна 50/200), расходы — исходные.
Подробности: [docs/lightweighting_flow_power_correlations.md](docs/lightweighting_flow_power_correlations.md).
Для разделения **энергетических вкладов** расхода и давления используйте
`export_lightweighting_energy_attribution.py`: `csv_files/lightweighting_energy_attribution.csv`,
20 пар 0%/30% × 4 движения. Сохранена обработка мощности 50/200; сумма вкладов
точно равна изменению энергии. Дополнительно приведены прямые разности углов
Lift/Tilt между случаями. Формулы и оценка сопоставимости траектории:
[docs/lightweighting_energy_attribution.md](docs/lightweighting_energy_attribution.md).
`export_valve_flow_energy_by_motion.py` создаёт `csv_files/valve_flow_energy_by_motion.csv`
с отклонениями расходов и разложением изменения энергии на вклады расхода и
давления для всех сценариев, четырёх движений и Lift/Tilt/суммы.
Определения и формулы: [docs/valve_flow_energy_metrics.md](docs/valve_flow_energy_metrics.md).

## `procedures_raw/` — исходные расчётные данные

| Процедура | Назначение |
|---|---|
| `export_lightweighting_energy_attribution.py` | Вклады расхода и давления в изменение энергии 0%/30% по движениям и прямое сравнение углов. |
| `plot_valve_supply_flows.py` | Отдельные графики расходов Lift/Tilt и отдельная общая легенда для четырёх сценариев. |
| `plot_boom_angle_scenarios.py` | Отдельные графики углов Lift/Tilt и отдельная общая легенда для четырёх сценариев. |
| `export_lightweighting_flow_power_correlations.py` | Корреляции изменений мощности насоса и расходов между парными сценариями 0%/30% по движениям. |
| `export_valve_flow_energy_by_motion.py` | Отклонения расходов и энергетические вклады расхода/давления по движениям в CSV. |
| `export_boom_angle_error_metrics.py` | RMSE, максимум абсолютной ошибки и средняя знаковая ошибка углов Lift/Tilt для всех сценариев в CSV. |
| `export_hydraulic_energy_balance.py` | Сводный энергетический баланс всех случаев `commitable_data` в CSV. |
| `export_hydraulic_energy_balance_by_motion.py` | Энергетический баланс каждого из четырёх движений для всех случаев в CSV. |
| `export_model_validation_metrics.py` | RMSE, максимальная ошибка и bias углов и давлений относительно эксперимента в CSV. |
| `plot_chamber_pressure_by_motion.py` | Средние давления по движениям и определение ведущей камеры LS. |
| `plot_pump_power_change.py` | Разность мощности насоса при облегчении на 30%. |
| `plot_pump_energy_change_by_motion.py` | Изменение энергии насоса по отдельным движениям. |
| `plot_pump_energy_change_surface.py` | Поверхность изменения энергии по облегчению и нагрузке. |
| `plot_pump_energy_change_heatmap.py` | Расчёт и карты изменения энергии по облегчению и нагрузке. |
| `plot_pump_energy_change_by_pressure.py` | Изменение энергии при облегчении в зависимости от давления. |
| `plot_valve_control_signals.py` | Сравнение управляющих сигналов с заданными. |
| `plot_valve_control_deviation_std.py` | Максимум, среднее абсолютное отклонение и стандартное отклонение коррекции PID. |
| `plot_valve_control_deviation_rms.py` | Вариант PID-статистики с RMS вместо стандартного отклонения. |
| `plot_boom_angles.py` | Сравнение угловых траекторий с заданными. |
| `plot_power_balance_hose_expansion.py` | Баланс мощности с оценкой расширения рукавов. |
| `plot_power_balance_hydraulic.py` | Гидравлический баланс по давлениям и расходам в узлах. |
| `plot_chamber_pressure_vs_load_sensing.py` | Сопоставление давлений камер с сигналом LS. |
| `plot_model_vs_experiment.py` | Сравнение модели с экспериментом из `exp_pressures/` и заданными углами. |
| `plot_hydraulic_energy_shares.py` | Доли энергии цилиндров и остаточных потерь по параметрам режима. |
| `plot_exported_pump_power.py` | График экспортированного сигнала мощности `Pump_P`. |
| `plot_calculated_pump_power.py` | Мощность насоса, вычисленная по давлению и расходу. |
| `plot_reference_angles_and_control.py` | Графики заданных углов и управляющих сигналов. |
| `plot_boom_angle_rmse_by_pressure.py` | Суммарная ошибка угловых траекторий в зависимости от давления. |

## `procedures_csv/` — готовые CSV

| Процедура | Назначение |
|---|---|
| `plot_pump_energy_change_bars_3d.py` | Объёмная диаграмма изменения энергии по облегчению и нагрузке. |
| `plot_pump_energy_change_heatmap.py` | Карты изменения энергии из `dW_by_LP_*.csv`. |
| `plot_pump_energy_change_by_pressure.py` | График изменения энергии по давлению. |
| `plot_boom_angle_rmse_by_pressure.py` | Графики ошибки угловых траекторий. |

## `utils/` — служебные функции и вспомогательные графики

| Файл | Назначение |
|---|---|
| `paths.py` | Корень проекта, выбор источника и пути результатов. |
| `data_import.py` | Копирование экспортов из внешнего каталога; явно задаваемое назначение может перезаписываться. |
| `result_parser.py` | Чтение таблиц, выбор расчётных случаев и загрузка заданных сигналов. |
| `processing.py` | Интерполяция, отсечение времени, фильтрация пиков, усреднение, расчёт мощности и энергии. |
| `plotting.py` | Общие функции построения графиков. |
| `plot_blocks.py` | Готовые группы графиков и сравнений энергозатрат, давлений и углов. |
| `plot_stribeck_friction.py` | Вспомогательный график заданной характеристики трения. |
