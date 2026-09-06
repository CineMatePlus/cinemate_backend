# Data notice

`app/ai/control/first_hundred.csv` contains a curated 999-movie subset derived
from the **Full TMDB Movies Dataset 2024 (1M Movies)** dataset published by
Asaniczka on Kaggle:

- Source: https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies
- Upstream license: Open Data Commons Attribution License (ODC-By)
- Derived file SHA-256: `85bb1130b8cc2b59621c1c94e5efad285103e8ad09f42634a7a6fd40769bc9aa`
- Transformation: the first 999 valid rows from the downloaded source snapshot,
  preserving the original 24 columns.

The checked-in seed was reproduced byte-for-byte with
`app/ai/control/first_hundred.py` from the locally retained, Git-ignored source
snapshot before publication.

The full upstream dataset is not redistributed by this repository. It remains
ignored by Git and Docker build contexts.

Movie metadata originates from [The Movie Database (TMDB)](https://www.themoviedb.org/).
This product uses the TMDB API/data but is not endorsed or certified by TMDB.
TMDB names and associated marks remain the property of their respective owners.

The repository's MIT license applies to the project source code. It does not
replace the upstream dataset license or TMDB attribution requirements.
