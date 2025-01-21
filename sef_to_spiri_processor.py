import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog, messagebox, Label, Entry, Button, ttk, simpledialog, BooleanVar


def process_files(shared_data):

    # Izračunavanje `budget_year` na osnovu `datum_ocekivanog_placanja`
    try:
        shared_data["budzetska_godina"] = shared_data["datum_ocekivanog_placanja"].split("-")[0]
    except Exception as e:
        messagebox.showerror("Greška", f"Nevažeći format datuma očekivanog plaćanja: {str(e)}")
        return

    # Izbor SEF XML fajlova preko GUI dijaloga
    xml_files = filedialog.askopenfilenames(title="Izaberite SEF XML fajlove", filetypes=[("XML files", "*.xml")])

    if not xml_files:
        messagebox.showwarning("Upozorenje", "Niste izabrali nijedan fajl!")
        return

    # Kreiraj root element za SPIRI XML
    cumulative_reason_code = "PO07" if shared_data["kreirati_zahtev"] else "PO05"
    spiri_root = ET.Element("commitments", {
        "cumulative_reason_code": cumulative_reason_code,
        "currency_code": "RSD",
        "treasury": "601",
        "budget_year": shared_data["budzetska_godina"],
        "budget_user_id": shared_data["jbkjs"]
    })

    for index, file in enumerate(xml_files, start=1):
        try:
            # Parsiranje SEF XML-a
            tree = ET.parse(file)
            sef_root = tree.getroot()
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške prilikom čitanja fajla {file}: {str(e)}")
            continue

        # Namespace za XPath
        namespaces = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "env": "urn:eFaktura:MinFinrs:envelop:schema"
        }

        # Izvlačenje podataka iz SEF XML-a
        try:
            invoice_number = sef_root.find(".//cbc:ID", namespaces).text
            account_number_element = sef_root.find(".//cac:PayeeFinancialAccount/cbc:ID", namespaces)
            account_number = account_number_element.text if account_number_element is not None else "000000000000000000"
            account_number = account_number[:3] + account_number[3:].replace("-", "").zfill(15)
            recipient = sef_root.find(".//cac:PartyName/cbc:Name", namespaces).text
            recipient_place = sef_root.find(".//cac:PostalAddress/cbc:CityName", namespaces).text
            amount = sef_root.find(".//cbc:PayableAmount", namespaces).text
            invoice_date = sef_root.find(".//cbc:IssueDate", namespaces).text
            due_date = sef_root.find(".//cbc:DueDate", namespaces).text
            contract_number = sef_root.find(".//cac:Contract/cbc:ID", namespaces)
            contract_number = contract_number.text if contract_number is not None else "N/A"
        except Exception as e:
            messagebox.showerror("Greška", f"Problem sa fajlom {file}: {str(e)}")
            continue

        # Dinamički unos economic_classification_code za svaki fajl
        economic_classification_code = simpledialog.askstring(
            "Unos ekonomske klasifikacije", f"Unesite ekonomsku klasifikaciju za fakturu {invoice_number}:"
        )
        if not economic_classification_code:
            messagebox.showerror("Greška", f"Ekonomska klasifikacija je obavezna za fakturu {invoice_number}!")
            return

        # Generisanje jedinstvenog `external_id`
        external_id = f"{invoice_number}-{index}"

        # Kreiranje commitment elementa za SPIRI
        commitment = ET.SubElement(spiri_root, "commitment", {
            "reason_code": "PO01",
            "external_id": external_id,
            "recipient": recipient,
            "recipient_place": recipient_place,
            "account_number": account_number,
            "invoice_number": invoice_number,
            "invoice_type": "3",
            "invoice_date": invoice_date,
            "due_date": due_date,
            "payment_code": shared_data["sifra_placanja"],
            "credit_model": "",
            "credit_reference_number": invoice_number,
            "payment_basis": f"Уплата по фактури број {invoice_number}"
        })

        # Dodavanje jednog item elementa
        item = ET.SubElement(commitment, "item")
        ET.SubElement(item, "budget_user_id").text = shared_data["jbkjs"]
        ET.SubElement(item, "program_code").text = shared_data["programski_kod"]
        ET.SubElement(item, "project_code").text = shared_data["projekat_kod"]
        ET.SubElement(item, "economic_classification_code").text = economic_classification_code
        ET.SubElement(item, "source_of_funding_code").text = shared_data["izvor_finansiranja"]
        ET.SubElement(item, "function_code").text = shared_data["funkcija"]
        ET.SubElement(item, "amount").text = amount
        ET.SubElement(item, "expected_payment_date").text = shared_data["datum_ocekivanog_placanja"]
        ET.SubElement(item, "urgent_payment").text = "false"
        ET.SubElement(item, "posting_account").text = "252111"
        ET.SubElement(item, "recording_account").text = shared_data["evidencioni_racun"]

    # Snimanje SPIRI XML fajla
    output_file = filedialog.asksaveasfilename(
        title="Sačuvajte SPIRI XML fajl", defaultextension=".xml", filetypes=[("XML files", "*.xml")]
    )
    if output_file:
        tree = ET.ElementTree(spiri_root)
        tree.write(output_file, encoding="UTF-8", xml_declaration=True)
        messagebox.showinfo("Uspeh", f"SPIRI XML fajl je uspešno sačuvan u:\n{output_file}")


def start_gui():
    root = Tk()
    root.title("SEF u SPIRI Konverter")
    root.geometry("700x500")
    root.resizable(False, False)

    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 12))

    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True, fill="both")

    shared_data = {}

    ttk.Label(frame, text="Broj budžetskog korisnika:").grid(row=0, column=0, pady=10, sticky="e")
    broj_budzetskog_korisnika = ttk.Entry(frame, width=30)
    broj_budzetskog_korisnika.grid(row=0, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Datum očekivanog plaćanja (YYYY-MM-DD):").grid(row=1, column=0, pady=10, sticky="e")
    datum_ocekivanog_placanja = ttk.Entry(frame, width=30)
    datum_ocekivanog_placanja.grid(row=1, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Šifra plaćanja:").grid(row=2, column=0, pady=10, sticky="e")
    sifra_placanja = ttk.Entry(frame, width=30)
    sifra_placanja.grid(row=2, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Program:").grid(row=3, column=0, pady=10, sticky="e")
    programski_kod = ttk.Entry(frame, width=30)
    programski_kod.grid(row=3, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Projektna aktivnost:").grid(row=4, column=0, pady=10, sticky="e")
    projekat_kod = ttk.Entry(frame, width=30)
    projekat_kod.grid(row=4, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Izvor finansiranja:").grid(row=5, column=0, pady=10, sticky="e")
    izvor_finansiranja = ttk.Entry(frame, width=30)
    izvor_finansiranja.grid(row=5, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Funkcija:").grid(row=6, column=0, pady=10, sticky="e")
    funkcija = ttk.Entry(frame, width=30)
    funkcija.grid(row=6, column=1, pady=10, sticky="w")

    ttk.Label(frame, text="Evidencioni račun:").grid(row=7, column=0, pady=10, sticky="e")
    evidencioni_racun = ttk.Entry(frame, width=30)
    evidencioni_racun.grid(row=7, column=1, pady=10, sticky="w")

    # Checkbox za kreiranje zahteva za plaćanje
    kreirati_zahtev = BooleanVar(value=True)
    ttk.Checkbutton(
        frame,
        text="Kreirati zahtev za plaćanje",
        variable=kreirati_zahtev
    ).grid(row=8, columnspan=2, pady=10)

    def submit_and_process():
        shared_data["jbkjs"] = broj_budzetskog_korisnika.get()
        shared_data["datum_ocekivanog_placanja"] = datum_ocekivanog_placanja.get()
        shared_data["sifra_placanja"] = sifra_placanja.get()
        shared_data["programski_kod"] = programski_kod.get()
        shared_data["projekat_kod"] = projekat_kod.get()
        shared_data["izvor_finansiranja"] = izvor_finansiranja.get()
        shared_data["funkcija"] = funkcija.get()
        shared_data["evidencioni_racun"] = evidencioni_racun.get()
        shared_data["kreirati_zahtev"] = kreirati_zahtev.get()
        process_files(shared_data)

    ttk.Button(frame, text="Generiši XML", command=submit_and_process).grid(row=9, columnspan=3, pady=20)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
