"""
Dashboard Page
==============
Main landing page showing KPI cards and analytical charts
(students per class, registrations, re-inscriptions, departures,
transport usage). All charts update dynamically with filters.
"""

import customtkinter as ctk
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utils.theme import COLORS, CHART_COLORS, font_title, font_subtitle, font_body
from models.dashboard_model import DashboardModel
from models.student import Student
from database.db_manager import DatabaseManager


class DashboardPage(ctk.CTkFrame):

    MONTHS_FR = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
        7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=("#F8FAFC", "#0F172A"), **kwargs)

        self.db = DatabaseManager()
        self.current_year = self.db.get_setting("current_school_year", "2025/2026")
        self.next_year = self.db.get_setting("next_school_year", "2026/2027")

        self.selected_year = ctk.StringVar(value=self.current_year)
        self.selected_class = ctk.StringVar(value="Toutes")
        now = datetime.now()
        self.selected_month_num = now.month
        self.selected_month = ctk.StringVar(value=self.MONTHS_FR[now.month])

        self.kpi_cards = {}
        self.chart_frames = {}

        self._build_header()
        self._build_filters()
        self._build_kpi_section()
        self._build_charts_section()

        self.refresh()

    # ------------------------------------------------------------------
    # Header & Filters
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))

        # School logo in dashboard header
        logo_path = self._get_logo_path()
        if logo_path:
            try:
                from PIL import Image
                from customtkinter import CTkImage
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((48, 48))
                self._logo_img = CTkImage(light_image=img, dark_image=img, size=(48, 48))
                ctk.CTkLabel(header, image=self._logo_img, text="").pack(side="left", padx=(0, 10))
            except Exception:
                pass

        ctk.CTkLabel(header, text="📊 Dashboard", font=font_title()).pack(side="left")

    def _get_logo_path(self):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ("logo.jpeg", "logo.jpg", "logo.png"):
            p = os.path.join(base, "assets", "icons", name)
            if os.path.exists(p):
                return p
        return None

    def _build_filters(self):
        filter_frame = ctk.CTkFrame(
            self, fg_color=("white", COLORS["card_dark"]), corner_radius=12,
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
        )
        filter_frame.pack(fill="x", padx=25, pady=10)

        inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        # School Year filter
        ctk.CTkLabel(inner, text="Année scolaire:", font=font_body()).pack(side="left", padx=(0, 8))
        years = [self.current_year, self.next_year]
        self.year_menu = ctk.CTkOptionMenu(
            inner, values=years, variable=self.selected_year,
            command=lambda v: self.refresh(), fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.year_menu.pack(side="left", padx=(0, 20))

        # Class filter
        ctk.CTkLabel(inner, text="Classe:", font=font_body()).pack(side="left", padx=(0, 8))
        self.class_menu = ctk.CTkOptionMenu(
            inner, values=["Toutes"], variable=self.selected_class,
            command=lambda v: self.refresh(), fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.class_menu.pack(side="left", padx=(0, 20))

        # Month filter
        ctk.CTkLabel(inner, text="Mois:", font=font_body()).pack(side="left", padx=(0, 8))
        month_values = [self.MONTHS_FR[m] for m in range(1, 13)]
        self.month_menu = ctk.CTkOptionMenu(
            inner, values=month_values, variable=self.selected_month,
            command=self._on_month_change, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"], width=130,
        )
        self.month_menu.pack(side="left", padx=(0, 20))

        # Refresh button
        ctk.CTkButton(
            inner, text="🔄 Actualiser", fg_color=COLORS["secondary"],
            hover_color=COLORS["primary_hover"], command=self.refresh, width=120,
        ).pack(side="right")

    def _on_month_change(self, value):
        for num, name in self.MONTHS_FR.items():
            if name == value:
                self.selected_month_num = num
                break
        self.refresh()

    # ------------------------------------------------------------------
    # KPI Cards
    # ------------------------------------------------------------------
    def _build_kpi_section(self):
        from views.widgets import KPICard

        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25, pady=10)

        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1)

        # Row 0 – student KPIs
        self.kpi_cards["enrolled"] = KPICard(
            kpi_frame, "Élèves inscrits (année actuelle)", "0",
            icon="🎓", color=COLORS["primary"],
        )
        self.kpi_cards["enrolled"].grid(row=0, column=0, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["pre_registered"] = KPICard(
            kpi_frame, "Pré-inscrits (année prochaine)", "0",
            icon="📋", color=COLORS["secondary"],
        )
        self.kpi_cards["pre_registered"].grid(row=0, column=1, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["new_this_month"] = KPICard(
            kpi_frame, "Nouvelles inscriptions ce mois", "0",
            icon="✨", color=COLORS["success"],
        )
        self.kpi_cards["new_this_month"].grid(row=0, column=2, padx=8, pady=5, sticky="nsew")

        self.kpi_cards["transport"] = KPICard(
            kpi_frame, "Élèves utilisant le transport", "0",
            icon="🚌", color=COLORS["warning"],
        )
        self.kpi_cards["transport"].grid(row=0, column=3, padx=8, pady=5, sticky="nsew")

        # Row 1 – financial KPIs (span 2 cols each for more display room)
        kpi_frame.grid_columnconfigure(0, weight=2)
        kpi_frame.grid_columnconfigure(1, weight=2)
        kpi_frame.grid_columnconfigure(2, weight=2)
        kpi_frame.grid_columnconfigure(3, weight=2)

        self.kpi_cards["inscription_revenue"] = KPICard(
            kpi_frame,
            "💳 Revenus d'inscription",
            "0 / 0 DH",
            icon="📝",
            color=COLORS["success"],
        )
        self.kpi_cards["inscription_revenue"].grid(
            row=1, column=0, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        self.kpi_cards["monthly_income"] = KPICard(
            kpi_frame,
            "💰 Revenus encaissés ce mois",
            "0 / 0 DH",
            icon="📈",
            color=COLORS["primary"],
        )
        self.kpi_cards["monthly_income"].grid(
            row=1, column=2, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        # Row 2 – Employee KPIs
        self.kpi_cards["nb_employes"] = KPICard(
            kpi_frame, "👥 Nombre d'Employés", "0",
            icon="👤", color="#7C3AED",
        )
        self.kpi_cards["nb_employes"].grid(
            row=2, column=0, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        self.kpi_cards["salaires_payes"] = KPICard(
            kpi_frame, "💼 Salaires Payés", "0 / 0 DH",
            icon="💵", color="#0891B2",
        )
        self.kpi_cards["salaires_payes"].grid(
            row=2, column=2, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        # Row 3 – Expense & Profit KPIs
        self.kpi_cards["depenses_payees"] = KPICard(
            kpi_frame, "📋 Dépenses Payées", "0 / 0 DH",
            icon="🏦", color="#DC2626",
        )
        self.kpi_cards["depenses_payees"].grid(
            row=3, column=0, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        self.kpi_cards["depenses_restantes"] = KPICard(
            kpi_frame, "⚠️ Dépenses Restantes", "0 DH",
            icon="🔔", color=COLORS["warning"],
        )
        self.kpi_cards["depenses_restantes"].grid(
            row=3, column=2, columnspan=2, padx=8, pady=5, sticky="nsew"
        )

        # Row 4 – Profit KPI (full width)
        self.kpi_cards["profit"] = KPICard(
            kpi_frame, "📊 Profit Net", "0 DH",
            icon="💹", color="#0891B2",
        )
        self.kpi_cards["profit"].grid(
            row=4, column=0, columnspan=4, padx=8, pady=5, sticky="nsew"
        )

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    def _build_charts_section(self):
        self.charts_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, padx=25, pady=10)

        for i in range(2):
            self.charts_container.grid_columnconfigure(i, weight=1)

        # Row 1: students per class (bar), monthly registrations (line)
        self.chart_frames["per_class"] = self._make_chart_card(self.charts_container, "Élèves par classe")
        self.chart_frames["per_class"].grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["monthly_reg"] = self._make_chart_card(self.charts_container, "Inscriptions mensuelles")
        self.chart_frames["monthly_reg"].grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        # Row 2: reinscription progress (donut), departures (line)
        self.chart_frames["reinscription"] = self._make_chart_card(self.charts_container, "Progression des réinscriptions")
        self.chart_frames["reinscription"].grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["departures"] = self._make_chart_card(self.charts_container, "Départs par mois")
        self.chart_frames["departures"].grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        # Row 3: transport by class (pie) - full width
        self.chart_frames["transport_class"] = self._make_chart_card(self.charts_container, "Élèves transport par classe")
        self.chart_frames["transport_class"].grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        # Row 4: Monthly income evolution (line), Payment status distribution (pie)
        self.chart_frames["income_evolution"] = self._make_chart_card(self.charts_container, "Évolution des revenus mensuels")
        self.chart_frames["income_evolution"].grid(row=3, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["payment_status"] = self._make_chart_card(self.charts_container, "Répartition des statuts de paiement")
        self.chart_frames["payment_status"].grid(row=3, column=1, padx=8, pady=8, sticky="nsew")

        # Row 4: income by class (bar) - full width
        self.chart_frames["income_by_class"] = self._make_chart_card(self.charts_container, "Revenus par classe")
        self.chart_frames["income_by_class"].grid(row=4, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        # Row 5: salary payment progress (bar)
        self.chart_frames["salary_progress"] = self._make_chart_card(self.charts_container, "Progression des Salaires (Payé / Impayé)")
        self.chart_frames["salary_progress"].grid(row=5, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        # Row 6: Expenses by category (bar) + Fixed vs Variable (pie)
        self.chart_frames["exp_by_category"] = self._make_chart_card(self.charts_container, "Dépenses par Catégorie")
        self.chart_frames["exp_by_category"].grid(row=6, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["exp_fixed_vs_var"] = self._make_chart_card(self.charts_container, "Fixe vs Variable")
        self.chart_frames["exp_fixed_vs_var"].grid(row=6, column=1, padx=8, pady=8, sticky="nsew")

        # Row 7: Monthly expense evolution (line) + Paid vs Unpaid (pie)
        self.chart_frames["exp_monthly_evo"] = self._make_chart_card(self.charts_container, "Évolution Mensuelle des Dépenses")
        self.chart_frames["exp_monthly_evo"].grid(row=7, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_frames["exp_paid_unpaid"] = self._make_chart_card(self.charts_container, "Dépenses Payées vs Non Payées")
        self.chart_frames["exp_paid_unpaid"].grid(row=7, column=1, padx=8, pady=8, sticky="nsew")

    def _make_chart_card(self, parent, title):
        card = ctk.CTkFrame(
            parent, corner_radius=14, fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
            height=340,
        )
        ctk.CTkLabel(card, text=title, font=font_subtitle()).pack(anchor="w", padx=18, pady=(15, 5))

        canvas_holder = ctk.CTkFrame(card, fg_color="transparent")
        canvas_holder.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        card.canvas_holder = canvas_holder
        card.canvas_widget = None
        return card

    def _render_chart(self, card, fig):
        """Embed a matplotlib figure inside a chart card, replacing previous one."""
        if card.canvas_widget is not None:
            card.canvas_widget.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=card.canvas_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        card.canvas_widget = canvas
        plt.close(fig)

    def _empty_fig(self, message="Aucune donnée disponible"):
        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="#94A3B8")
        ax.axis("off")
        return fig

    # ------------------------------------------------------------------
    # Refresh / Data loading
    # ------------------------------------------------------------------
    def refresh(self):
        year = self.selected_year.get()

        # Update class filter options
        classes = ["Toutes"] + Student.get_distinct_classes(year)
        self.class_menu.configure(values=classes)
        if self.selected_class.get() not in classes:
            self.selected_class.set("Toutes")

        self._update_kpis(year)
        self._update_charts(year)

    def _update_kpis(self, year):
        # ── Student KPIs ─────────────────────────────────────────────
        try:
            now            = datetime.now()
            enrolled       = DashboardModel.kpi_current_year_count(year)
            pre_registered = DashboardModel.kpi_pre_registered_next_year(self.next_year)
            new_this_month = DashboardModel.kpi_new_registrations_this_month(
                year, now.year, self.selected_month_num
            )
            transport = DashboardModel.kpi_transport_users(year)

            self.kpi_cards["enrolled"].update_value(enrolled)
            self.kpi_cards["pre_registered"].update_value(pre_registered)
            self.kpi_cards["new_this_month"].update_value(new_this_month)
            self.kpi_cards["transport"].update_value(transport)
        except Exception:
            pass

        # ── Financial KPIs ────────────────────────────────────────────
        try:
            from models.payment import Payment
            from utils.payment_constants import MONTH_CALENDAR_MAP

            classe          = self.selected_class.get()
            sel_month_name  = self.selected_month.get()

            # ── KPI 1: Revenus d'inscription ──────────────────────────
            # = SUM(inscription_amount from Excel) + SUM(app Inscription payments)
            # displayed as  "value / grand_total"
            insc_value = Payment.total_inscription_revenue(year, classe)
            insc_total = Payment.total_inscription_grand_total(year)
            self.kpi_cards["inscription_revenue"].update_value(
                f"{insc_value:,.0f} / {insc_total:,.0f} DH"
            )
            # Also update the card subtitle to show the selected month name
            self.kpi_cards["inscription_revenue"].title_label.configure(
                text=f"💳 Revenus d'inscription"
            )

            # ── KPI 2: Revenus encaissés ce mois ─────────────────────
            # = SUM(total_a_payer WHERE month_status[selected_month]=PAYE)
            #   + SUM(app Mensualité/Transport payments in that calendar month)
            # displayed as  "value / SUM(total_a_payer all students)"
            monthly_value = Payment.monthly_revenue_total(year, sel_month_name, classe)
            monthly_total = Payment.total_a_payer_sum(year, classe)
            self.kpi_cards["monthly_income"].update_value(
                f"{monthly_value:,.0f} / {monthly_total:,.0f} DH"
            )
            self.kpi_cards["monthly_income"].title_label.configure(
                text=f"💰 Revenus encaissés – {sel_month_name}"
            )

            # Debug log (printed to console for validation)
            debug = Payment.debug_kpi(year, sel_month_name, classe)
            print(
                f"[KPI DEBUG] year={year} month={sel_month_name} classe={classe}\n"
                f"  Inscription: imported={debug['inscription']['imported']:,.0f}  "
                f"app={debug['inscription']['app_created']:,.0f}  "
                f"total={debug['inscription']['total']:,.0f}  "
                f"display='{debug['inscription']['display']}'\n"
                f"  Monthly:     imported_payé={debug['monthly']['imported_paye']:,.0f}  "
                f"app={debug['monthly']['app_created']:,.0f}  "
                f"total={debug['monthly']['total']:,.0f}  "
                f"total_a_payer={debug['monthly']['total_a_payer']:,.0f}  "
                f"display='{debug['monthly']['display']}'"
            )
        except Exception as e:
            print(f"[KPI ERROR] {e}")

        # ── Employee & Salary KPIs ────────────────────────────────────
        try:
            from models.employee import Employee
            from models.salary_payment import SalaryPayment

            nb_emp = Employee.count_active()
            self.kpi_cards["nb_employes"].update_value(nb_emp)

            # Salary KPI: paid this month / total budget
            # Respect the selected month filter
            sel_month_name = self.selected_month.get()
            from utils.payment_constants import MONTH_CALENDAR_MAP
            start_yr = int(year.split("/")[0])
            end_yr   = int(year.split("/")[1])
            if sel_month_name in MONTH_CALENDAR_MAP:
                _, offset  = MONTH_CALENDAR_MAP[sel_month_name]
                sal_year   = str(start_yr if offset == 0 else end_yr)
            else:
                sal_year = str(datetime.now().year)

            paid_sal  = SalaryPayment.total_paid(month=sel_month_name, year=sal_year)
            total_sal = SalaryPayment.total_salary_budget()
            self.kpi_cards["salaires_payes"].update_value(
                f"{paid_sal:,.0f} / {total_sal:,.0f} DH"
            )
            self.kpi_cards["salaires_payes"].title_label.configure(
                text=f"💼 Salaires Payés – {sel_month_name}"
            )
        except Exception as e:
            print(f"[SALARY KPI ERROR] {e}")

        # ── Expense & Profit KPIs ──────────────────────────────────────
        try:
            from models.expense import Expense
            from models.salary_payment import SalaryPayment as SP
            from models.payment import Payment

            exp_total  = Expense.total_expenses(annee_scolaire=year)
            exp_paid   = Expense.total_paid_expenses(annee_scolaire=year)
            exp_unpaid = exp_total - exp_paid
            exp_count_unpaid = Expense.count_unpaid(annee_scolaire=year)

            self.kpi_cards["depenses_payees"].update_value(
                f"{exp_paid:,.0f} / {exp_total:,.0f} DH"
            )
            self.kpi_cards["depenses_restantes"].update_value(
                f"{exp_unpaid:,.0f} DH  ({exp_count_unpaid} impayées)"
            )

            # ── Profit = Revenus Encaissés - Dépenses Payées - Salaires Payés
            # Revenus encaissés: sum total_a_payer for import-paid months
            #   + app payments, for the full year
            all_months_revenue = sum(
                Payment.monthly_revenue_total(year, m)
                for m in [
                    "Septembre","Octobre","Novembre","Décembre",
                    "Janvier","Février","Mars","Avril","Mai","Juin"
                ]
            )
            sal_paid_total = SP.total_paid(year=year.split("/")[0]) + \
                             SP.total_paid(year=year.split("/")[1])
            insc_rev = Payment.total_inscription_revenue(year)
            total_revenue = insc_rev + all_months_revenue

            current_profit = total_revenue - exp_paid   - sal_paid_total
            total_profit   = total_revenue - exp_total  - SP.total_salary_budget()

            self.kpi_cards["profit"].update_value(
                f"{current_profit:,.0f} DH  (encaissé)  |  "
                f"{total_profit:,.0f} DH  (projeté)"
            )
            self.kpi_cards["profit"].title_label.configure(
                text=f"📊 Profit Net – {sel_month_name} {year}"
            )
        except Exception as e:
            print(f"[EXPENSE KPI ERROR] {e}")

    def _update_charts(self, year):
        # 1. Students per class - Bar Chart
        data = DashboardModel.students_per_class(year)
        if self.selected_class.get() != "Toutes":
            data = [(c, n) for c, n in data if c == self.selected_class.get()]
        self._render_bar_chart(self.chart_frames["per_class"], data)

        # 2. Monthly registrations - Line Chart
        data = DashboardModel.monthly_registrations(year)
        self._render_line_chart(self.chart_frames["monthly_reg"], data, COLORS["primary"])

        # 3. Reinscription progress - Donut Chart
        reinscribed, eligible = DashboardModel.reinscription_progress(year, self.next_year)
        self._render_donut_chart(self.chart_frames["reinscription"], reinscribed, eligible)

        # 4. Departures by month - Line Chart
        data = DashboardModel.departures_by_month(year)
        self._render_line_chart(self.chart_frames["departures"], data, COLORS["danger"])

        # 5. Transport users by class - Pie Chart
        data = DashboardModel.transport_users_by_class(year)
        self._render_pie_chart(self.chart_frames["transport_class"], data)

        # 6. Monthly income evolution - Line Chart (3 series)
        from models.payment import Payment
        classe = self.selected_class.get()
        income_data = Payment.monthly_income_evolution(year, classe)
        self._render_income_evolution_chart(self.chart_frames["income_evolution"], income_data)

        # 7. Payment status distribution - Pie Chart
        status_data = Payment.payment_status_distribution(year, classe)
        self._render_payment_status_chart(self.chart_frames["payment_status"], status_data)

        # 8. Income by class - Bar Chart
        income_by_class = Payment.income_by_class(year)
        self._render_income_by_class_chart(self.chart_frames["income_by_class"], income_by_class)

        # 9. Salary payment progress - Stacked Bar Chart
        try:
            from models.salary_payment import SalaryPayment as SP
            sal_data = SP.salary_progress_by_month(year)
            self._render_salary_progress_chart(self.chart_frames["salary_progress"], sal_data)
        except Exception:
            pass

        # 10–13. Expense charts
        try:
            from models.expense import Expense
            self._render_exp_by_category(
                self.chart_frames["exp_by_category"],
                Expense.expenses_by_category(year),
            )
            self._render_exp_fixed_vs_var(
                self.chart_frames["exp_fixed_vs_var"],
                Expense.expenses_by_type(year),
            )
            self._render_exp_monthly_evo(
                self.chart_frames["exp_monthly_evo"],
                Expense.monthly_expense_evolution(year),
            )
            self._render_exp_paid_unpaid(
                self.chart_frames["exp_paid_unpaid"],
                Expense.total_paid_expenses(year),
                Expense.total_expenses(year) - Expense.total_paid_expenses(year),
            )
        except Exception as e:
            print(f"[EXPENSE CHART ERROR] {e}")

    # ------------------------------------------------------------------
    # Chart renderers
    # ------------------------------------------------------------------
    def _render_bar_chart(self, card, data):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        bars = ax.bar(labels, values, color=COLORS["primary"], width=0.55)
        ax.bar_label(bars, padding=2, fontsize=8)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_line_chart(self, card, data, color):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.plot(labels, values, marker="o", color=color, linewidth=2)
        ax.fill_between(range(len(values)), values, alpha=0.1, color=color)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_donut_chart(self, card, reinscribed, eligible):
        remaining = max(eligible - reinscribed, 0)
        if eligible == 0:
            self._render_chart(card, self._empty_fig())
            return

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        values = [reinscribed, remaining]
        labels = ["Réinscrits", "En attente"]
        colors = [COLORS["success"], COLORS["border_light"]]
        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
            colors=colors, startangle=90, wedgeprops=dict(width=0.4),
        )
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
        ax.text(0, 0, f"{reinscribed}/{eligible}", ha="center", va="center", fontsize=14, fontweight="bold")
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_pie_chart(self, card, data):
        if not data:
            self._render_chart(card, self._empty_fig())
            return
        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(8, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        colors = CHART_COLORS[: len(values)]
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90,
               textprops={"fontsize": 8})
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_income_evolution_chart(self, card, data):
        """data: list of dicts {month, inscription, mensualite, transport, total}"""
        if not data or all(d["total"] == 0 for d in data):
            self._render_chart(card, self._empty_fig())
            return

        labels = [d["month"] for d in data]
        inscription = [d["inscription"] for d in data]
        mensualite = [d["mensualite"] for d in data]
        transport = [d["transport"] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.plot(labels, inscription, marker="o", label="Inscription", color=COLORS["secondary"], linewidth=2)
        ax.plot(labels, mensualite, marker="o", label="Mensualité", color=COLORS["success"], linewidth=2)
        ax.plot(labels, transport, marker="o", label="Transport", color=COLORS["warning"], linewidth=2)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.legend(fontsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_payment_status_chart(self, card, status_data):
        """status_data: {'PAYE': n, 'UNPAID': n, 'NAN': n}"""
        from utils.payment_constants import STATUS_PAYE, STATUS_UNPAID, STATUS_NAN, STATUS_LABELS, STATUS_COLORS

        values = [status_data.get(STATUS_PAYE, 0), status_data.get(STATUS_UNPAID, 0), status_data.get(STATUS_NAN, 0)]
        if sum(values) == 0:
            self._render_chart(card, self._empty_fig())
            return

        labels = [STATUS_LABELS[STATUS_PAYE], STATUS_LABELS[STATUS_UNPAID], STATUS_LABELS[STATUS_NAN]]
        colors = [STATUS_COLORS[STATUS_PAYE], STATUS_COLORS[STATUS_UNPAID], STATUS_COLORS[STATUS_NAN]]

        # Filter out zero-value slices to avoid clutter
        filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        labels, values, colors = zip(*filtered)

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors, startangle=90,
               textprops={"fontsize": 8})
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_income_by_class_chart(self, card, data):
        """data: list of (classe, total_revenue)"""
        data = [(c, v) for c, v in data if v > 0]
        if not data:
            self._render_chart(card, self._empty_fig())
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = Figure(figsize=(10, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        bars = ax.bar(labels, values, color=COLORS["success"], width=0.6)
        ax.bar_label(bars, padding=2, fontsize=7, fmt="%.0f")
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)
    def _render_salary_progress_chart(self, card, data):
        """
        data: list of {month, paid, unpaid}
        Stacked bar chart showing paid vs unpaid salary per month.
        """
        if not data or all(d["paid"] == 0 and d["unpaid"] == 0 for d in data):
            self._render_chart(card, self._empty_fig("Aucune donnée de salaire disponible"))
            return

        labels = [d["month"] for d in data]
        paid   = [d["paid"]   for d in data]
        unpaid = [d["unpaid"] for d in data]

        fig = Figure(figsize=(10, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax  = fig.add_subplot(111)

        x = range(len(labels))
        ax.bar(x, paid,   color=COLORS["success"], label="Payé",   width=0.5)
        ax.bar(x, unpaid, color=COLORS["danger"],  label="Impayé", width=0.5, bottom=paid)

        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=8)
        fig.tight_layout()
        self._render_chart(card, fig)

    # ── Expense chart renderers ────────────────────────────────────────
    def _render_exp_by_category(self, card, data):
        """Bar chart: total expense per category."""
        data = [(c, v) for c, v in data if v > 0]
        if not data:
            self._render_chart(card, self._empty_fig()); return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]
        fig    = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        bars = ax.barh(labels, values, color="#7C3AED")
        ax.bar_label(bars, padding=3, fontsize=7, fmt="%.0f")
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=7)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_exp_fixed_vs_var(self, card, data):
        """Pie chart: Fixe vs Variable expenses."""
        vals   = [data.get("Fixe", 0), data.get("Variable", 0)]
        if sum(vals) == 0:
            self._render_chart(card, self._empty_fig()); return

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax  = fig.add_subplot(111)
        ax.pie(vals, labels=["Fixe", "Variable"],
               colors=["#7C3AED", "#F59E0B"],
               autopct="%1.0f%%", startangle=90,
               textprops={"fontsize": 9})
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_exp_monthly_evo(self, card, data):
        """Stacked line chart: paid + unpaid expenses per school month."""
        if not data or all(d["total"] == 0 for d in data):
            self._render_chart(card, self._empty_fig()); return

        labels = [d["month"] for d in data]
        paid   = [d["paid"]   for d in data]
        unpaid = [d["unpaid"] for d in data]

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax  = fig.add_subplot(111)
        ax.plot(labels, paid,   marker="o", color=COLORS["success"],
                label="Payé",    linewidth=2)
        ax.plot(labels, unpaid, marker="o", color=COLORS["danger"],
                label="Non Payé", linewidth=2)
        ax.set_facecolor("none")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=7)
        fig.tight_layout()
        self._render_chart(card, fig)

    def _render_exp_paid_unpaid(self, card, paid, unpaid):
        """Pie chart: paid vs unpaid expense amounts."""
        if paid + unpaid == 0:
            self._render_chart(card, self._empty_fig()); return

        fig = Figure(figsize=(5, 3), dpi=80)
        fig.patch.set_alpha(0)
        ax  = fig.add_subplot(111)
        ax.pie([paid, unpaid],
               labels=["Payé", "Non Payé"],
               colors=[COLORS["success"], COLORS["danger"]],
               autopct="%1.0f%%", startangle=90,
               textprops={"fontsize": 9})
        fig.tight_layout()
        self._render_chart(card, fig)
