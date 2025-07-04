# data-download

Python script to query and download **Sentinel-2** and **Landsat** data.

- **Sentinel-2 data** are downloaded from the [Copernicus Dataspace Ecosystem (CDSE)](https://dataspace.copernicus.eu/).
- **Landsat data** are downloaded from the [USGS Earth Explorer](https://earthexplorer.usgs.gov/).

---

## 🔐 Credentials Setup

To run this code, you need valid credentials for **CDSE** and **USGS Earth Explorer**.

To securely manage your credentials, **store them in a `.env` file** — this keeps sensitive data out of your source code and version control.

In the **root** of your project, create a file named `.env` and add your credentials:

\`\`\`env
# .env
ERS_USERNAME=xxxxx
ERS_TOKEN=xxxxx
CDSE_USERNAME=xxxxx
CDSE_PASSWORD=xxxxx
\`\`\`

👉 **Get your ERS token:** [USGS M2M Application Token Documentation](https://www.usgs.gov/media/files/m2m-application-token-documentation)

---

## 📥 Cloning the Repository

\`\`\`bash
git clone git@github.com:vpremier/data-download.git
cd data-download/
conda env create -f download.yml
conda activate download
spyder
\`\`\`

Alternatively, create your own Conda environment and install the required libraries manually. Add any extra dependencies as needed.

---

## 🛠️ Setting Up the Code

Before running `main.py`, configure:

- **Date range** for the query.
- (Optional) **Shapefile path** for your area of interest.
- **Output directory**.
- Filter by **tile** (Sentinel-2) or **path/row** (Landsat).
- For other flags/parameters, check `utils.py`.


