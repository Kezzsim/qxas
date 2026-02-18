from tiled.client import from_uri
from databroker import Broker

from xas.process import process_interpolate_bin_from_uid
# from xas.tiled_io import load_interpolated_df_from_tiled


# test uid provided by ?? on Februrary ??
uid = ""

# Create tiled client objects
client = from_uri("https://tiled.nsls2.bnl.gov")
qas_raw = client["qas/raw"]

# Wrap tiled client for QAS raw data in the databroker
# backward-compatible wrapper.
db = Broker(qas_raw)


def test():
    # TEST WRITING
    "Load raw data, align columns by interpolating and binning, and save the result."
    process_interpolate_bin_from_uid(uid, db)

    # TEST READING
    # "Read the processed data back from tiled with the method isstools uses"
    # (a, b) = load_interpolated_df_from_tiled("foil Se-K 0001-r0002.raw")
    # print(a)
    # print(b)


if __name__ == "__main__":
    test()
