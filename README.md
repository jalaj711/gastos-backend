<h1 style="text-align: center">Gastos</h1>
<p style="text-align: center">An app to suite all your expense (finances in general) tracking needs with support for multiple wallets and custom color-coded labels.</p>

This repository hosts source code for the REST API of the Gastos app.

## Getting Started

First, install the dependencies:

```bash
pyhton3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then apply the migrations:

```bash
python manage.py migrate
```

And finally, run the development server:

```bash
python manage.py runserver
```

This will start the API server for the app


**Note:**

This is only the backend part of the entire app, the frontend can be found [here](https://github.com/jalaj711/gastos-frontend). You will need to install the backend to be able to run the frontend. The frontend will by default re-route all API requests to [http://127.0.0.1:8000](http://127.0.0.1:8000). Make sure that this is the port on which django is running.

## License

This project is available under the MIT License. Full text can be found [here](LICENSE).

## Contributing

Being an open source project, we are open to all kinds of contributions.

If you have found any bug or want to request a feature feel free to open an [issue](https://github.com/jalaj711/gastos-backend/issues/new).

If you would like to get your hands dirty with code, then head on to the [issues](https://github.com/jalaj711/gastos-backend/issues/) section and send us a PR, we would be more than happy to accept it :)

