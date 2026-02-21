from flask import Flask, render_template, request, Response
import ipaddress
import csv
import io
from vlsm import vlsm_calculate
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

def calculate_subnet(ip_input):
    try:
        network = ipaddress.ip_network(ip_input, strict=False)
        ip = ipaddress.ip_address(ip_input.split("/")[0])
        hosts = list(network.hosts())
        return {
            "ip": str(ip),
            "network": str(network.network_address),
            "broadcast": str(network.broadcast_address),
            "subnet_mask": str(network.netmask),
            "wildcard": str(network.hostmask),
            "cidr": network.prefixlen,
            "first_host": str(hosts[0]) if hosts else "N/A",
            "last_host": str(hosts[-1]) if hosts else "N/A",
            "num_hosts": max(network.num_addresses - 2, 0),
            "ip_type": "Private" if ip.is_private else "Public",
            "error": None
        }
    except ValueError as e:
        return {"error": str(e)}

def parse_vlsm_form(form):
    vlsm_network = form.get("vlsm_network", "").strip()
    names = form.getlist("req_name")
    hosts = form.getlist("req_hosts")
    requirements = []
    for name, host in zip(names, hosts):
        if name and host:
            try:
                requirements.append({"name": name, "hosts": int(host)})
            except ValueError:
                pass
    return vlsm_network, requirements

@app.route("/", methods=["GET", "POST"])
def index():
    subnet_result = None
    vlsm_result = None
    user_input = ""
    active_tab = "subnet"

    if request.method == "POST":
        if "ip_input" in request.form:
            active_tab = "subnet"
            user_input = request.form.get("ip_input", "").strip()
            if " " in user_input:
                parts = user_input.split()
                prefix = ipaddress.IPv4Network(f"0.0.0.0/{parts[1]}").prefixlen
                user_input = f"{parts[0]}/{prefix}"
            subnet_result = calculate_subnet(user_input)

        elif "vlsm_network" in request.form:
            active_tab = "vlsm"
            vlsm_network, requirements = parse_vlsm_form(request.form)
            if requirements:
                vlsm_result = vlsm_calculate(vlsm_network, requirements)

    return render_template("index.html",
                           subnet_result=subnet_result,
                           vlsm_result=vlsm_result,
                           user_input=user_input,
                           active_tab=active_tab)

@app.route("/export/csv", methods=["POST"])
def export_csv():
    vlsm_network, requirements = parse_vlsm_form(request.form)
    result = vlsm_calculate(vlsm_network, requirements)

    if result.get("error"):
        return result["error"], 400

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Network", "CIDR", "Subnet Mask", "First Host", "Last Host", "Usable Hosts", "Needed", "Wasted"])
    for s in result["subnets"]:
        writer.writerow([s["name"], s["network"], f"/{s['cidr']}", s["subnet_mask"],
                         s["first_host"], s["last_host"], s["usable_hosts"], s["needed_hosts"], s["wasted"]])

    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=vlsm_plan.csv"})

@app.route("/export/pdf", methods=["POST"])
def export_pdf():
    vlsm_network, requirements = parse_vlsm_form(request.form)
    result = vlsm_calculate(vlsm_network, requirements)

    if result.get("error"):
        return result["error"], 400

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("VLSM Subnet Plan", styles["Title"]))
    elements.append(Paragraph(f"Base Network: {result['network']}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Total Hosts Needed: {result['total_needed']}  |  Allocated: {result['total_allocated']}  |  Efficiency: {result['efficiency']}%", styles["Normal"]))
    elements.append(Spacer(1, 20))

    table_data = [["Name", "Network/CIDR", "Subnet Mask", "Host Range", "Usable", "Needed", "Wasted"]]
    for s in result["subnets"]:
        table_data.append([
            s["name"],
            f"{s['network']}/{s['cidr']}",
            s["subnet_mask"],
            f"{s['first_host']} - {s['last_host']}",
            str(s["usable_hosts"]),
            str(s["needed_hosts"]),
            str(s["wasted"])
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=vlsm_plan.pdf"})

if __name__ == "__main__":
    app.run(debug=True)