from flask import *
from flask_bootstrap import Bootstrap
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, HttpResponseError
from azure.data.tables import TableServiceClient
from azure.data.tables import TableClient

app = Flask(__name__)
Bootstrap(app)

ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif"]
app.config["SECRET_KEY"] = "SECRET_KEY"

#blob storage
container_name = "photos" # container name in which images will be store in the storage account
connect_str = "DefaultEndpointsProtocol=https;AccountName=gccproiect1;AccountKey=abh6M/9b3K6SWL60tffb0b5tSjZmv/FxMal+R1+cfWzAmQTv3w8wuRr7J0H8rHhbNsVDC9ggre/u+AStahypbw==;EndpointSuffix=core.windows.net"

#blob client
blob_service_client = BlobServiceClient.from_connection_string(conn_str=connect_str) # create a blob service client to interact with the storage account
try:
    container_client = blob_service_client.get_container_client(container=container_name) 
    container_client.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
except Exception as e:
    container_client = blob_service_client.create_container(container_name) 

#table storage
table_service_client = TableServiceClient.from_connection_string(conn_str=connect_str)
table_client = table_service_client.get_table_client(table_name="table1")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gallery/")
def gallery():
    blob_items = container_client.list_blobs() # list all the blobs in the container and display in reversed order
    lst = [blob for blob in blob_items]
    lst.sort(key=lambda x: x.creation_time, reverse=True) 
    entities = list(table_client.list_entities())
    entities.reverse()
    din_doi = []
    for el in entities:
        print(el['RowKey'])
        din_doi.append(el['RowKey'])
    din_primul = []
    for blob in lst:
        blob_client = container_client.get_blob_client(blob=blob.name).url
        din_primul.append(blob_client)
    pairs = list(zip(din_primul, din_doi))
    

    return render_template("gallery.html", gallery= pairs)


@app.route("/upload/", methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        description = request.form.get("description")
        image = request.files["image"]
        try:
            container_client.upload_blob(image.filename, image) # upload the file to the container using the filename as the blob name
            flash("Successfully uploaded image to gallery!", "success")
            blob_items = container_client.list_blobs()
            lst = [blob for blob in blob_items]
            lst.sort(key=lambda x: x.creation_time, reverse=True)
            blob_client = container_client.get_blob_client(blob=lst[0].name)
            print(blob_client.url)
            print(description)
            my_entity = {
                'PartitionKey':'elements' ,
                'RowKey': description,
                'url':blob_client.url,
            }
            try:
                resp = table_client.create_entity(entity=my_entity)
            except ResourceExistsError:
                print("Entity already exists")
            entities = list(table_client.list_entities())
            print("no of entities"+ str(len(entities)))
            for i, entity in enumerate(entities):
                print("Entity #{}: {}".format(entity, i))
            return redirect(url_for("upload"))
        except Exception as e:
            print(e)
            print("Ignoring duplicate filenames") 
            flash("An error occurred while uploading the image!", "danger")
            return redirect(url_for("upload"))
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)