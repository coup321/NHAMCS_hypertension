import os
import pandas as pd
import requests
from zipfile import ZipFile


class FileDownloader():
    def __init__(self, base_url, files_to_download, download_directory):
        self.base_url = base_url
        self.files_to_download = files_to_download
        self.download_directory = download_directory
        self.zip_filenames = []
        self.spss_filenames = []

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def download_zipped_files(self):
        for file in self.files_to_download:
            url = f'{self.base_url}{file}'
            local_file = os.path.join(
                self.download_directory, 'zipped_files', file)
            self.zip_filenames.append(local_file)

            if not os.path.exists(local_file):
                print(f'Downloading {file}...')
                response = requests.get(url)
                with open(local_file, 'wb') as f:
                    f.write(response.content)
                print(f'Finished downloading {file}')

    def file_unzipper(self):
        spss_file = os.path.join(self.download_directory, 'spss_files')
        sav_files = [x.replace('.zip', '.sav') for x in self.files_to_download]

        for file, sav_file in zip(self.zip_filenames, sav_files):

            self.spss_filenames.append(os.path.join(spss_file, sav_file))
            with ZipFile(file, 'r') as zip_ref:
                print(f'Unzipping {file}...')
                zip_ref.extractall(spss_file)
                print(f'Finished unzipping {file}.')

    def file_pickler(self):

        pkl_files = [x.replace('.zip', '.pkl') for x in self.files_to_download]
        for file, pkl_file in zip(self.spss_filenames, pkl_files):
            pickle_root = os.path.join(
                self.download_directory, 'pickled_files'
            )
            pickle_file = os.path.join(pickle_root, pkl_file)
            print(f'Pickling {pickle_root}...')
            if not os.path.exists(pickle_file):
                df = pd.read_spss(file)
                df.to_pickle(pickle_file)
            print(f'Finished pickling {pickle_root}...')

    def run(self):
        # make sure the base directory exists + make it if needed
        self.check_directory(self.download_directory)
        # make sure the zip directory exists + make it if needed
        self.check_directory(os.path.join(
            self.download_directory, 'zipped_files'))
        # make sure the spss directory exists + make it if needed
        self.check_directory(os.path.join(
            self.download_directory, 'spss_files'))
        # make sure the pickle directory exists + make it if needed
        self.check_directory(os.path.join(
            self.download_directory, 'pickled_files'))
        # download files
        print(f'Downloading spss zip files from: {self.base_url}')
        self.download_zipped_files()
        # unzip files
        print('Unzipping spss files')
        self.file_unzipper()
        # pickle files
        print('Converting spss files to pickled dataframes')
        self.file_pickler()

    def __call__(self):
        self.run()


if __name__ == '__main__':
    base_url = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/dataset_documentation/nhamcs/spss/"
    files_to_download = [
        'ed2015-spss.zip', 'ed2016-spss.zip', 'ED2017-spss.zip',
        'ED2018-spss.zip', 'ED2019-spss.zip', 'ed2020-spss.zip',
        'ed2021-spss.zip'
    ]
    download_directory = './data/'

    downloader = FileDownloader(base_url, files_to_download, download_directory)
    downloader()
