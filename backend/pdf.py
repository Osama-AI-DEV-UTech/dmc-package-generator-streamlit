"""Render ONE package -> ONE enterprise-style PDF.

The layout is intentionally label-driven so an automated extraction service can
read every field back reliably: each value sits next to an explicit label, the
itinerary is "Day N" delimited, and a compact DATA SHEET lists the scalar fields.
"""
from __future__ import annotations

import os
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

from .schema import DMCInfo, Package, PriceReference

INK = colors.HexColor("#15233a")
ACCENT = colors.HexColor("#c9772f")
ACCENT2 = colors.HexColor("#1f6f6b")
SOFT = colors.HexColor("#fbf2e9")
TEAL_SOFT = colors.HexColor("#eaf4f3")
MUTED = colors.HexColor("#6a778c")
LINE = colors.HexColor("#e3e7ee")
DARK = colors.HexColor("#0f1a2b")


def _styles():
    s = getSampleStyleSheet()
    def add(n, **kw): s.add(ParagraphStyle(n, parent=s["Normal"], **kw))
    add("Hero", fontName="Helvetica-Bold", fontSize=23, textColor=colors.white, leading=26)
    add("HeroSub", fontSize=10.5, textColor=colors.HexColor("#f3e3d4"), leading=15)
    add("Eyebrow", fontName="Helvetica-Bold", fontSize=8.5, textColor=ACCENT, spaceAfter=2)
    add("H1", fontName="Helvetica-Bold", fontSize=14, textColor=INK, spaceBefore=12, spaceAfter=5)
    add("H2", fontName="Helvetica-Bold", fontSize=10.5, textColor=DARK, spaceBefore=5, spaceAfter=2)
    add("Body", fontSize=9.5, textColor=INK, leading=14, spaceAfter=4)
    add("Small", fontSize=8.4, textColor=MUTED, leading=11.6)
    add("Cell", fontSize=8.6, textColor=INK, leading=11.6)
    add("Mono", fontName="Courier", fontSize=7.6, textColor=INK, leading=10)
    return s


def _money(v, cur):
    if v is None:
        return "—"
    try:
        return f"{cur} {float(v):,.0f}"
    except (TypeError, ValueError):
        return str(v)


def _tbl(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 8.6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), INK),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT])]
    t.setStyle(TableStyle(style))
    return t


def _hero(pkg: Package, st):
    dest = ", ".join(c.value for d in pkg.destinations for c in d.city) or \
        (pkg.destinations[0].country.value if pkg.destinations else "")
    nights = max(pkg.numberOfDays - 1, 0)
    tags = " · ".join(m.value for m in pkg.packageMood) or "Tour Package"
    inner = [
        [Paragraph("UBIDTOURS · READY GROUND PACKAGE", st["HeroSub"])],
        [Paragraph(pkg.name, st["Hero"])],
        [Paragraph(f"{dest} &nbsp;|&nbsp; {pkg.numberOfDays} Days / {nights} Nights "
                   f"&nbsp;|&nbsp; Group up to {pkg.groupSize}", st["HeroSub"])],
        [Paragraph(tags, st["HeroSub"])],
    ]
    it = Table(inner, colWidths=[170 * mm])
    it.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 16),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                            ("TOPPADDING", (0, 0), (0, 0), 16),
                            ("BOTTOMPADDING", (0, -1), (-1, -1), 16),
                            ("TOPPADDING", (0, 1), (-1, -1), 1)]))
    band = Table([[it]], colWidths=[170 * mm])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK),
                              ("LINEBELOW", (0, 0), (-1, -1), 3, ACCENT),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return band


def _dmc_card(dmc: Optional[DMCInfo], st) -> list:
    flow = [Paragraph("OFFERED BY (DMC)", st["Eyebrow"])]
    if not dmc:
        flow.append(Paragraph("DMC details not available for this package.", st["Small"]))
        return flow
    badge = "✔ verified from live source" if dmc.verified else "to be verified"
    rows = [
        ["DMC name", dmc.name or "—"],
        ["Legal name", dmc.legal_name or "—"],
        ["Specialisation", dmc.specialisation or "—"],
        ["Phone", dmc.phone or "—"],
        ["WhatsApp", dmc.whatsapp or "—"],
        ["Email", dmc.email or "—"],
        ["Website", dmc.website or "—"],
        ["Address", dmc.address or "—"],
        ["City / Country", f"{dmc.city or '—'} / {dmc.country or '—'}"],
        ["Languages", ", ".join(dmc.languages) or "—"],
        ["Why recommended", dmc.why_recommended or "—"],
        ["Source", dmc.source_url or "—"],
        ["Status", badge],
    ]
    body = [[Paragraph(f"<b>{k}</b>", st["Cell"]), Paragraph(str(v), st["Cell"])] for k, v in rows]
    t = Table(body, colWidths=[42 * mm, 128 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), TEAL_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, ACCENT2),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    flow.append(t)
    return flow


def _data_sheet(pkg: Package, cur, st, include_prices: bool = True) -> list:
    """Compact label:value scalars for deterministic ingestion."""
    rows = [
        ("skuId", pkg.skuId), ("packageId", pkg.packageId),
        ("name", pkg.name), ("numberOfDays", pkg.numberOfDays),
        ("seatsPerTour", pkg.seatsPerTour), ("groupSize", pkg.groupSize),
        ("region", pkg.destinations[0].regions.value if pkg.destinations else ""),
        ("country", pkg.destinations[0].country.value if pkg.destinations else ""),
        ("cities", ", ".join(c.value for d in pkg.destinations for c in d.city)),
        ("packageMood", ", ".join(m.value for m in pkg.packageMood)),
        ("pkgType", ", ".join(t.value for t in pkg.pkgType)),
        ("ageRange", pkg.ageRange.value), ("childAgeRange", pkg.childAgeRange.value),
        ("isChildFriendly", pkg.isChildFriendly), ("isInsuranceRequired", pkg.isInsuranceRequired),
        ("isHandicapAccessible", pkg.isHandicapAccessible), ("isActive", pkg.isActive),
        ("isTopRated", pkg.isTopRated),
    ]
    if include_prices:
        rows += [
            ("currency", cur),
            ("basePrice", pkg.basePrice), ("childDiscountPrice", pkg.childDiscountPrice),
            ("infantDiscountPrice", pkg.infantDiscountPrice),
            ("singleSuplimentPrc", pkg.singleSuplimentPrc),
            ("adminBasePrice", pkg.adminBasePrice),
            ("adminChildDiscountPrice", pkg.adminChildDiscountPrice),
            ("adminInfantDiscountPrice", pkg.adminInfantDiscountPrice),
        ]
    lines = "<br/>".join(f"{k}: {v}" for k, v in rows)
    flow = [Paragraph("DATA SHEET (FOR INGESTION)", st["Eyebrow"]),
            Paragraph("Structured fields", st["H1"]),
            Paragraph(lines, st["Mono"])]
    return flow


def build_package_pdf(pkg: Package, dmc: Optional[DMCInfo],
                      refs: List[PriceReference], sources: List[str],
                      currency: str, out_dir: str, request_id: str, index: int,
                      engine: str = "", mode: str = "full") -> str:
    """mode='full' -> everything (your copy). mode='dmc' -> no DMC card, no prices."""
    is_full = mode != "dmc"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{request_id}_pkg{index}_{mode}.pdf")
    st = _styles()
    cur = currency or (refs[0].currency if refs else "USD")

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=14 * mm, bottomMargin=14 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm, title=pkg.name)
    flow = [_hero(pkg, st), Spacer(1, 8)]
    copy_label = "FULL COPY · with pricing & DMC" if is_full else "OPERATOR (DMC) COPY · no pricing, no DMC details"
    flow.append(Paragraph(f"Package ID: {pkg.packageId} &nbsp;·&nbsp; SKU: {pkg.skuId} "
                          f"&nbsp;·&nbsp; {copy_label}", st["Small"]))
    flow.append(Spacer(1, 6))

    # DMC card (full copy only)
    if is_full:
        flow.extend(_dmc_card(dmc, st))

    # Overview
    flow.append(Paragraph("OVERVIEW", st["Eyebrow"]))
    flow.append(Paragraph("About this package", st["H1"]))
    flow.append(Paragraph(pkg.tourDetail or "—", st["Body"]))
    if pkg.tourPlan.arrival:
        flow.append(Paragraph(f"<b>Arrival:</b> {pkg.tourPlan.arrival}", st["Small"]))
    if pkg.tourPlan.departure:
        flow.append(Paragraph(f"<b>Departure:</b> {pkg.tourPlan.departure}", st["Small"]))

    # Itinerary
    if pkg.itineraryDetail:
        flow.append(Paragraph("ITINERARY", st["Eyebrow"]))
        flow.append(Paragraph("Day by day", st["H1"]))
        for d in pkg.itineraryDetail:
            flow.append(KeepTogether([Paragraph(f"Day {d.day}", st["H2"]),
                                      Paragraph(d.detail, st["Body"])]))

    # Accommodation
    if pkg.tourPlan.accommodation:
        flow.append(Paragraph("ACCOMMODATION", st["Eyebrow"]))
        flow.append(Paragraph("Hotels", st["H1"]))
        rows = [["Hotel", "City", "Nights"]]
        for a in pkg.tourPlan.accommodation:
            rows.append([Paragraph(a.serviceId or "—", st["Cell"]),
                         Paragraph(a.city.value, st["Cell"]), str(a.noOfNights)])
        flow.append(_tbl(rows, [95 * mm, 50 * mm, 25 * mm]))

    # Transportation
    if pkg.transportation:
        flow.append(Paragraph("TRANSPORTATION", st["Eyebrow"]))
        flow.append(Paragraph("Transfers", st["H1"]))
        rows = [["Day", "From", "To", "Type"]]
        for tr in pkg.transportation:
            types = ", ".join(t.value for t in tr.availableType)
            rows.append([str(tr.day), Paragraph(tr.from_.location, st["Cell"]),
                         Paragraph(tr.to.location, st["Cell"]), Paragraph(types, st["Cell"])])
        flow.append(_tbl(rows, [12 * mm, 54 * mm, 54 * mm, 50 * mm]))

    # Meals
    ms = pkg.mealSummary
    flow.append(Paragraph("MEALS", st["Eyebrow"]))
    flow.append(Paragraph("Dining", st["H1"]))
    flow.append(Paragraph("<b>Preferences:</b> "
                          + (", ".join(p.value for p in ms.availableMealPref) or "Standard"),
                          st["Body"]))
    for label, m in [("Breakfast", ms.breakfast), ("Lunch", ms.lunch), ("Dinner", ms.dinner)]:
        if m.numberOfMeals or m.desc:
            flow.append(Paragraph(f"<b>{label} ({m.numberOfMeals}):</b> {m.desc}", st["Small"]))

    # Inclusions / exclusions
    ts = pkg.travelService
    if ts.included or ts.notIncluded:
        flow.append(Paragraph("WHAT'S INCLUDED", st["Eyebrow"]))
        flow.append(Paragraph("Inclusions & exclusions", st["H1"]))
        inc = "<br/>".join(f"✓ {i}" for i in ts.included) or "—"
        exc = "<br/>".join(f"✗ {i}" for i in ts.notIncluded) or "—"
        two = Table([[Paragraph("<b>Included</b><br/>" + inc, st["Small"]),
                      Paragraph("<b>Not included</b><br/>" + exc, st["Small"])]],
                    colWidths=[85 * mm, 85 * mm])
        two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("BACKGROUND", (0, 0), (0, 0), TEAL_SOFT),
                                 ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fdf0ec")),
                                 ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                                 ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                                 ("TOPPADDING", (0, 0), (-1, -1), 9),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 10)]))
        flow.append(two)

    # Availability
    if pkg.packageAvailability:
        av = pkg.packageAvailability[0]
        flow.append(Paragraph("AVAILABILITY", st["Eyebrow"]))
        flow.append(Paragraph("When it runs", st["H1"]))
        flow.append(Paragraph("<b>Days:</b> " + (", ".join(d.value for d in av.pkgDays) or "—"), st["Small"]))
        flow.append(Paragraph("<b>Months:</b> " + (", ".join(m.value for m in av.pkgMonths) or "—"), st["Small"]))
        flow.append(Paragraph("<b>Years:</b> " + (", ".join(y.value for y in av.pkgYears) or "—"), st["Small"]))

    # Pricing (full copy only)
    if is_full:
        flow.append(Paragraph("PRICING", st["Eyebrow"]))
        flow.append(Paragraph("Package rates", st["H1"]))
        flow.append(Paragraph(
            f"<font size=20 color='#1f6f6b'><b>{_money(pkg.basePrice, cur)}</b></font>"
            f"<font size=9 color='#6a778c'> &nbsp;net per person (from)</font>",
            ParagraphStyle("PriceBig", parent=st["Body"], leading=26, spaceAfter=6)))
        flow.append(_tbl([
            ["Rate", "Net (DMC)", "Selling (Admin)"],
            ["Base / person", _money(pkg.basePrice, cur), _money(pkg.adminBasePrice, cur)],
            ["Child", _money(pkg.childDiscountPrice, cur), _money(pkg.adminChildDiscountPrice, cur)],
            ["Infant", _money(pkg.infantDiscountPrice, cur), _money(pkg.adminInfantDiscountPrice, cur)],
            ["Single supplement", _money(pkg.singleSuplimentPrc, cur), "—"],
        ], [70 * mm, 50 * mm, 50 * mm]))

    # Price references (full copy only)
    if is_full and refs:
        flow.append(Paragraph("PRICE REFERENCES", st["Eyebrow"]))
        flow.append(Paragraph("How prices were estimated", st["H1"]))
        rows = [["Item", "Estimate", "Basis", "Source"]]
        for r in refs:
            rows.append([Paragraph(r.item, st["Cell"]), _money(r.estimate, r.currency or cur),
                         Paragraph(r.basis or "—", st["Cell"]),
                         Paragraph(f"<font size=7>{r.source_url or '—'}</font>", st["Cell"])])
        flow.append(_tbl(rows, [50 * mm, 26 * mm, 34 * mm, 60 * mm]))

    # Policy
    if pkg.policy.pkg:
        flow.append(Paragraph("POLICY", st["Eyebrow"]))
        flow.append(Paragraph("Booking & cancellation", st["H1"]))
        flow.append(Paragraph(pkg.policy.pkg, st["Small"]))

    # Data sheet
    flow.append(Spacer(1, 6))
    flow.extend(_data_sheet(pkg, cur, st, include_prices=is_full))

    # Footer
    flow.append(Spacer(1, 8))
    flow.append(HRFlowable(width="100%", thickness=0.6, color=LINE))
    if is_full:
        foot = ("Prices are AI estimates from the listed sources; confirm with the DMC "
                "before selling. Generated by UBIDTOURS Package Generator.")
    else:
        foot = ("Operator copy — pricing and DMC details intentionally omitted. Share with "
                "operators to collect quotes. Generated by UBIDTOURS Package Generator.")
    flow.append(Paragraph(foot, st["Small"]))
    doc.build(flow)
    return path
