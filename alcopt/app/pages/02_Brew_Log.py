import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from unum import units
import logging
import traceback

from sqlalchemy import asc

from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    Fermentation,
    Ingredient,
    IngredientAddition,
    MassMeasurement,
    SpecificGravityMeasurement,
)
from alcopt.streamlit_utils import (
    all_container_log_info,
    all_containers_info,
    all_ingredient_additions_info,
    all_sg_measurement_info,
)
from alcopt.database.utils import (
    all_mass_measurement_info,
    close_open_log,
    current_fermentation_log,
    get_db,
)
from alcopt.utils import (
    abv_to_sugar,
    BENCHMARK,
    YEAST,
    str2unit,
    calculate_max_potential_abv,
)
from alcopt.auth import show_login_status, is_admin

st.set_page_config(
    page_title="Brew Tracking",
    page_icon="🍷",
)

token = show_login_status()

if not token:
    st.warning("🔒 Please log in to access this page.")
    st.stop()

if not is_admin():
    st.error("🔒 Admin Page")
    st.stop()

logging.info(
    f"{st.session_state.get('user_email', 'unknown')} Accessed Brew Tracking Page"
)

if "new_ingredients" not in st.session_state:
    st.session_state.new_ingredients = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None


def add_new_ingredient(db):
    with st.form("Add New Ingredient"):
        ingredient_name = st.text_input("New Ingredient Name")
        sugar_content = st.number_input("Sugar Content (g/L or g)", value=0.0)
        ingredient_type = st.radio("Type", ["Liquid", "Solute", "Solid"])
        density = st.number_input("Density (g/mL)", value=1.0)
        price = st.number_input("Price ($/L, kg, or unit)", value=0.00)
        notes = st.text_input("Additional Notes")
        if st.form_submit_button("Add"):
            if ingredient_name is not None and ingredient_name != "":
                try:
                    new_ingredient = Ingredient(
                        name=ingredient_name,
                        sugar_content=sugar_content,
                        ingredient_type=ingredient_type,
                        density=density,
                        price=price,
                        notes=notes,
                    )
                    db.add(new_ingredient)
                    db.commit()
                    logging.info(
                        f"{st.session_state.get('user_email', 'unknown')} added new ingredient: {ingredient_name}"
                    )
                except Exception as e:
                    print(traceback.format_exc())
                    st.error(e)
                    logging.error(f"An error occurred: {e}")


def start_fermentation_form():
    """Explicitly create a new fermentation in a container.

    Replaces the implicit fermentation-creation that used to happen on first
    ingredient add. Opens a new ContainerFermentationLog row, closing any
    previously-open one on that container.
    """
    with st.form("start_fermentation_form"):
        container_id = st.number_input(
            "Container ID", value=1, min_value=1, step=1, key="start_ferm_container_id"
        )
        date = st.date_input("Start Date", key="start_ferm_date")
        stage = st.text_input("Stage", value="primary", key="start_ferm_stage")
        if st.form_submit_button("Start Fermentation"):
            with get_db() as db:
                try:
                    container = db.query(Container).filter_by(id=container_id).first()
                    if container is None:
                        st.error(f"Container {container_id} not found")
                        return
                    start_dt = datetime.combine(date, datetime.min.time())
                    new_ferm = Fermentation(start_date=date)
                    db.add(new_ferm)
                    db.flush()
                    close_open_log(db, container_id, start_dt)
                    db.add(
                        ContainerFermentationLog(
                            container_id=container_id,
                            fermentation_id=new_ferm.id,
                            start_date=start_dt,
                            stage=stage,
                        )
                    )
                    db.commit()
                    st.success(
                        f"Started Fermentation {new_ferm.id} in Container {container_id}"
                    )
                    logging.info(
                        f"{st.session_state.get('user_email', 'unknown')} started fermentation {new_ferm.id} in container {container_id}"
                    )
                except Exception as e:
                    db.rollback()
                    st.error(f"Error: {e}")
                    logging.error(f"An error occurred: {e}")


def add_ingredient_addition_form(ingredient_name=None):
    """Add an ingredient to a container at a specific time.

    The container does NOT need to currently hold a fermentation. This is the
    core flexibility ask: pre-fermentation soak, post-bottling priming sugar,
    aging additions, etc. all flow through this single form.
    """
    with st.form("Add Ingredient"):
        with get_db() as db:
            container_id = st.number_input("Container ID", value=1, min_value=1, step=1)
            if ingredient_name is None:
                ingredient_name = st.text_input("Ingredient Name")
            date = st.date_input("Date")
            col_start, col_end = st.columns([1, 1])
            start_amount = col_start.number_input(
                "Starting Amount", value=0.0, min_value=0.0
            )
            end_amount = col_end.number_input("Ending Amount", value=0.0, min_value=0.0)
            amount = end_amount - start_amount
            unit = st.text_input("Units", "g")
            if st.form_submit_button("Add"):
                try:
                    container = db.query(Container).filter_by(id=container_id).first()
                    if container is None:
                        st.error(f"Container {container_id} not found")
                        return
                    ingredient = (
                        db.query(Ingredient).filter_by(name=ingredient_name).first()
                    )
                    if ingredient is None:
                        st.error(f"Ingredient '{ingredient_name}' not found")
                        return
                    added_at = datetime.combine(date, datetime.now().time())
                    addition = IngredientAddition(
                        container_id=container_id,
                        ingredient_id=ingredient.id,
                        amount=amount,
                        unit=unit,
                        added_at=added_at,
                    )
                    db.add(addition)
                    db.commit()
                    active = current_fermentation_log(db, container_id, added_at)
                    if active is not None:
                        st.success(
                            f"Added to Container {container_id} (fermentation {active.fermentation_id})"
                        )
                    else:
                        st.success(
                            f"Added to Container {container_id} (no active fermentation)"
                        )
                    logging.info(
                        f"{st.session_state.get('user_email', 'unknown')} added ingredient: {ingredient_name} to container: {container_id}"
                    )
                except Exception as e:
                    db.rollback()
                    st.error(f"Error {e}")
                    logging.error(f"An error occurred: {e}")


def add_sg_measurement_form(db):
    st.title("Add Specific Gravity Measurement")

    with st.form(key="measurement_form"):
        container_id = st.number_input(
            "Container ID", value=1, min_value=1, step=1, key="sg_container_id"
        )
        measurement_date = st.date_input("Measurement Date", value=datetime.now())
        specific_gravity = st.number_input(
            "Specific Gravity", value=0.999, min_value=0.0, step=0.001, format="%.3f"
        )

        submit_button = st.form_submit_button(label="Add Measurement")

    if submit_button:
        try:
            container = db.query(Container).filter_by(id=container_id).first()
            if container is None:
                st.error(f"Container {container_id} not found")
                return
            measured_at = datetime.combine(measurement_date, datetime.now().time())
            log = current_fermentation_log(db, container_id, measured_at)
            if log is None:
                st.error(
                    f"Container {container_id} has no active fermentation at {measurement_date}"
                )
                return
            new_measurement = SpecificGravityMeasurement(
                fermentation_id=log.fermentation_id,
                measurement_date=measurement_date,
                specific_gravity=specific_gravity,
            )
            db.add(new_measurement)
            db.commit()
            st.success(f"Measurement added for Fermentation {log.fermentation_id}")
            logging.info(
                f"{st.session_state.get('user_email', 'unknown')} added SG measurement to container: {container_id}"
            )
        except Exception as e:
            db.rollback()
            st.error(f"An error occurred: {e}")
            logging.error(f"An error occurred: {e}")


def add_mass_measurement_form(db):
    st.title("Add Mass Measurement")

    with st.form(key="mass_measurement_form"):
        container_id = st.number_input(
            "Container ID", value=1, min_value=1, step=1, key="mass_container_id"
        )
        measurement_date = st.date_input("Measurement Date", value=datetime.now())
        mass = st.number_input(
            "Mass (g)", value=0.0, min_value=0.0, step=0.1, format="%.1f"
        )

        submit_button = st.form_submit_button(label="Add Mass Measurement")

    if submit_button:
        try:
            container = db.query(Container).filter_by(id=container_id).first()
            if container is None:
                st.error(f"Container {container_id} not found")
                return
            measured_at = datetime.combine(measurement_date, datetime.now().time())
            log = current_fermentation_log(db, container_id, measured_at)
            if log is None:
                st.error(
                    f"Container {container_id} has no active fermentation at {measurement_date}"
                )
                return
            new_mass_measurement = MassMeasurement(
                fermentation_id=log.fermentation_id,
                measurement_date=measurement_date,
                mass=mass,
            )
            db.add(new_mass_measurement)
            db.commit()
            st.success(f"Mass measurement added for Fermentation {log.fermentation_id}")
            logging.info(
                f"{st.session_state.get('user_email', 'unknown')} added mass measurement to container: {container_id}"
            )
        except Exception as e:
            db.rollback()
            st.error(f"An error occurred: {e}")
            logging.error(f"An error occurred: {e}")


def rack_form(db):
    """Move a fermentation from one container to another.

    Closes the source container's open log, opens a new log on the destination
    with the same fermentation_id and `source_container_id` set for traceability.
    """
    with st.form(key="rack_form"):
        col_from, col_to = st.columns((1, 1))
        from_container_id = col_from.number_input(
            "From Container ID", value=1, min_value=1, step=1
        )
        to_container_id = col_to.number_input(
            "To Container ID", value=1, min_value=1, step=1
        )
        date = st.date_input("Date", key="rack_date")
        stage = st.text_input("Stage", value="secondary", key="rack_stage")
        submit_button = st.form_submit_button(label="Add Action")

    if submit_button:
        try:
            from_container = db.query(Container).filter_by(id=from_container_id).first()
            to_container = db.query(Container).filter_by(id=to_container_id).first()
            if not from_container:
                st.error(f"Container {from_container_id} not found")
                return
            if not to_container:
                st.error(f"Container {to_container_id} not found")
                return
            at = datetime.combine(date, datetime.now().time())
            from_log = current_fermentation_log(db, from_container_id, at)
            if from_log is None:
                st.error(f"Container {from_container_id} has no active fermentation")
                return
            fermentation_id = from_log.fermentation_id
            close_open_log(db, from_container_id, at)
            close_open_log(db, to_container_id, at)
            db.add(
                ContainerFermentationLog(
                    container_id=to_container_id,
                    fermentation_id=fermentation_id,
                    start_date=at,
                    source_container_id=from_container_id,
                    stage=stage,
                )
            )
            db.commit()
            st.success(
                f"Racked fermentation {fermentation_id} from {from_container_id} to {to_container_id}"
            )
            logging.info(
                f"{st.session_state.get('user_email', 'unknown')} racked from container: {from_container_id} to container: {to_container_id}"
            )
        except Exception as e:
            db.rollback()
            st.error(f"An error occurred: {e}")
            logging.error(f"An error occurred: {e}")


def bottle_form(db):
    """Bottle (or otherwise transfer a portion) from one container to another.

    Unlike rack, this does NOT close the source's log — the source vessel may
    still hold liquid. Opens a new log on the destination container with
    `stage='bottled'` and a recorded amount.
    """
    with st.form(key="bottle_form"):
        from_container_id = st.number_input(
            "From Container ID (vessel)",
            value=1,
            min_value=1,
            step=1,
            key="bottle_from",
        )
        to_container_id = st.number_input(
            "To Container ID (bottle)", value=1, min_value=1, step=1, key="bottle_to"
        )
        date = st.date_input("Date", key="bottle_date")
        amount = st.number_input("Amount", value=0.0, min_value=0.0)
        unit = st.text_input("Units", "g", key="bottle_unit")
        submit_button = st.form_submit_button(label="Add Action")

    if submit_button:
        try:
            from_container = db.query(Container).filter_by(id=from_container_id).first()
            to_container = db.query(Container).filter_by(id=to_container_id).first()
            if not from_container:
                st.error(f"Container {from_container_id} not found")
                return
            if not to_container:
                st.error(f"Container {to_container_id} not found")
                return
            at = datetime.combine(date, datetime.now().time())
            from_log = current_fermentation_log(db, from_container_id, at)
            if from_log is None:
                st.error(f"Container {from_container_id} has no active fermentation")
                return
            close_open_log(db, to_container_id, at)
            db.add(
                ContainerFermentationLog(
                    container_id=to_container_id,
                    fermentation_id=from_log.fermentation_id,
                    start_date=at,
                    source_container_id=from_container_id,
                    amount=amount,
                    unit=unit,
                    stage="bottled",
                )
            )
            db.commit()
            st.success(
                f"Bottled fermentation {from_log.fermentation_id} from {from_container_id} into {to_container_id}"
            )
            logging.info(
                f"{st.session_state.get('user_email', 'unknown')} bottled from container: {from_container_id} to container: {to_container_id}"
            )
        except Exception as e:
            db.rollback()
            st.error(f"An error occurred: {e}")
            logging.error(f"An error occurred: {e}")

    empty_container_id = st.number_input(
        "Container ID to Empty",
        value=1,
        min_value=1,
        step=1,
        key="empty_container_id",
    )
    if st.button("Empty Container"):
        container = db.query(Container).filter_by(id=empty_container_id).first()
        if not container:
            st.error(f"Container {empty_container_id} not found")
            return
        closed = close_open_log(db, empty_container_id, datetime.now())
        db.commit()
        if closed is not None:
            st.success(
                f"Container {empty_container_id} emptied (closed log {closed.id})"
            )
        else:
            st.info(f"Container {empty_container_id} had no open log")


def display_ingredient_calculator():
    st.title("Fermentation Ingredient Calculator")

    container_id = st.number_input("Container ID", min_value=1, step=1)

    with get_db() as db:
        container = db.query(Container).filter_by(id=container_id).first()
        if not container:
            st.error("No container found with the given ID.")
            return

        max_container_volume = container.volume_liters * units.L

        ingredients = db.query(Ingredient).all()

    st.write(
        f"Maximum Container Volume: {max_container_volume.asNumber(units.L):.2f} L"
    )

    ingredient_options = {ingredient.name: ingredient for ingredient in ingredients}
    selected_ingredient_names = st.multiselect(
        "Select Ingredients", list(ingredient_options.keys())
    )

    selected_ingredients = []
    for name in selected_ingredient_names:
        ingredient = ingredient_options[name]
        col_unit, col_amount = st.columns([1, 3])
        unit = col_unit.selectbox(
            f"Unit for {ingredient.name}",
            options=["g", "mL"],
            key=f"{ingredient.id}_unit",
        )

        amount = col_amount.number_input(
            f"Amount of {ingredient.name} ({unit})",
            min_value=0.0,
            step=1.0,
            key=f"{ingredient.id}_amount",
        )
        selected_ingredients.append(
            {
                "id": ingredient.id,
                "name": ingredient.name,
                "sugar_content": ingredient.sugar_content
                * (
                    1.0
                    if ingredient.ingredient_type in ["Solute", "Solid"]
                    else units.g / units.L
                ),
                "amount": amount * str2unit[unit],
                "ingredient_type": ingredient.ingredient_type,
                "density": ingredient.density * units.kg / units.L,
            }
        )

    if selected_ingredients:
        max_abv, max_sugar_content, fermentation_volume = calculate_max_potential_abv(
            selected_ingredients
        )

        st.write(
            f"Current Total Volume: {fermentation_volume.asNumber(units.L)} liters"
        )

        if fermentation_volume > max_container_volume * 1000:
            st.error("Error: Total volume exceeds the maximum container volume!")
        elif fermentation_volume > 0.9 * max_container_volume * 1000:
            st.warning(
                "Warning: Total volume is above 90% of the maximum container volume!"
            )

        if max_abv == 0:
            st.error("No valid ingredients added to calculate ABV and sugar content.")
            return

        desired_abv = st.slider(
            "Desired ABV (%)",
            min_value=0.0,
            max_value=float(max_abv),
            step=0.1,
            key="desired_abv",
        )

        resulting_sugar_content = max_sugar_content - abv_to_sugar(desired_abv)
        st.write(
            f"**Resulting Sugar Content:** {resulting_sugar_content.asNumber(units.g / units.L):.2f} g/L"
        )

        max_sugar = max_sugar_content.asNumber(units.g / units.L)
        st.write(f"**Maximum Potential ABV:** {max_abv.asNumber():.2f}%")
        st.write(f"**Maximum Sugar Content:** {max_sugar:.2f} g/L")

        fig, ax = plt.subplots()
        for item in BENCHMARK:
            if item["abv"] is None:
                ax.axhline(item["rs"].asNumber(), color="black", alpha=0.7)
                ax.text(
                    0,
                    item["rs"].asNumber(),
                    f"{item['name']}",
                    color="black",
                    verticalalignment="bottom",
                )
            else:
                ax.scatter(item["abv"], item["rs"].asNumber(), c="lightskyblue")
                ax.text(
                    item["abv"],
                    item["rs"].asNumber(),
                    f"{item['name']}",
                    color="blue",
                    verticalalignment="bottom",
                )

        for item in YEAST:
            ax.axvline(item["max_abv"], color="orange", alpha=0.7)
            ax.text(
                item["max_abv"],
                0,
                f"{item['name']}",
                rotation=90,
                color="orange",
                verticalalignment="bottom",
            )

        resulting_sugar = resulting_sugar_content.asNumber(units.g / units.L)
        ax.scatter(desired_abv, resulting_sugar, c="green")
        ax.text(
            desired_abv,
            resulting_sugar,
            "Calculation",
            color="green",
            verticalalignment="bottom",
        )
        ax.plot([0, max_abv], [max_sugar, 0], color="green", linestyle="--")
        ax.set_ylabel("Residual Sugar (g/L)")
        ax.set_xlabel("ABV (%)")
        ax.set_xlim([0, None])
        ax.set_ylim([0, None])
        st.pyplot(fig)


(
    tab_start,
    tab_ingredient,
    tab_calc,
    tab_measurement,
    tab_mass,
    tab_rack,
    tab_bottle,
) = st.tabs(["Start", "Ingredient", "Calculator", "SG", "Mass", "Rack", "Bottle"])

with get_db() as db:
    with tab_start:
        start_fermentation_form()
        st.dataframe(all_container_log_info(db)[::-1], hide_index=True)

    with tab_ingredient:
        ingredient_names = [
            i.name for i in db.query(Ingredient).order_by(asc(Ingredient.name)).all()
        ]

        options = ingredient_names + ["*New Ingredient"]
        ingredient_name = st.selectbox("Ingredient Added", options=options)

        if ingredient_name == "*New Ingredient":
            add_new_ingredient(db)

        add_ingredient_addition_form(ingredient_name=ingredient_name)

        st.dataframe(all_ingredient_additions_info(db)[::-1], hide_index=True)

    with tab_measurement:
        add_sg_measurement_form(db)
        st.dataframe(all_sg_measurement_info(db)[::-1], hide_index=True)

    with tab_calc:
        display_ingredient_calculator()

    with tab_mass:
        add_mass_measurement_form(db)
        st.dataframe(all_mass_measurement_info(db)[::-1], hide_index=True)

    with tab_rack:
        rack_form(db)
        st.dataframe(all_container_log_info(db)[::-1], hide_index=True)

    with tab_bottle:
        bottle_form(db)
        st.dataframe(all_containers_info(db, container_type="bottle"), hide_index=True)
