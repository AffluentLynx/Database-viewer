#['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'], data=[], style=Pack(height=400))
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox  # Import for displaying a confirmation dialog
import sqlite3


class SQLiteViewer(tk.Tk):
    def __init__(self, database_filename):
        super().__init__()
        self.database_filename = database_filename
        self.title(f'SQLite Viewer - {self.database_filename}')
        self.geometry("700x300")  # Set the initial window size
    
        # Dropdown for table selection
        self.table_list = ttk.Combobox(self)
        self.table_list['values'] = self.get_table_names()
        self.table_list.bind('<<ComboboxSelected>>', self.on_table_select)
        self.table_list.grid(row=0, column=0, padx=10, pady=3, sticky='ew')
    
        # Edit Row button
        self.edit_button = ttk.Button(self, text='Edit Row', command=self.enable_editing)
        self.edit_button.grid(row=1, column=1, padx=10, pady=3, sticky='ew')
        self.editing_enabled = False
        self.editing_item = None
        self.edit_button.config(state=tk.DISABLED)
    
        # Text field for row range
        self.row_range_entry = ttk.Entry(self)
        self.row_range_entry.grid(row=1, column=0, padx=10, pady=3, sticky='ew')
        self.row_range_entry.bind('<Return>', self.on_row_range_entry_enter)
    
        # Remove Rows button (plural)
        self.remove_rows_button = ttk.Button(self, text='Remove Rows', command=self.remove_selected_rows)
        self.remove_rows_button.grid(row=1, column=2, padx=10, pady=3, sticky='ew')
    
        # Delete Table button
        self.delete_table_button = ttk.Button(self, text='Delete Table', command=self.delete_selected_table)
        self.delete_table_button.grid(row=0, column=1, padx=10, pady=3, sticky='ew')
    
        # Table view
        self.table_view = ttk.Treeview(
            self,
            columns=('Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'),
            show='headings'
        )

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.table_view.yview)
    
        # Packing the UI
        self.table_view.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')
        self.scrollbar.grid(row=2, column=4, sticky='ns')
    
        # Linking the scroll bar to its functionality
        self.table_view.configure(yscrollcommand=self.scrollbar.set)
    
        # Configure grid row/column weights for stretching
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)



    def on_row_range_entry_enter(self, event):
        range_text = self.row_range_entry.get()
        self.highlight_rows_by_range(range_text)

    def on_row_select(self, event):
        selected_items = self.table_view.selection()
        if selected_items:
            selected_indices = [self.table_view.item(item, 'values')[0] for item in selected_items]
            self.index_entry.delete(0, 'end')
            self.index_entry.insert(0, ', '.join(map(str, selected_indices)))

    
    def enable_editing(self):
        if not self.editing_enabled:
            selected_items = self.table_view.selection()
            if len(selected_items) == 1:
                self.editing_item = selected_items[0]
                self.editing_enabled = True
                self.edit_button.config(text='Save Edit')
                self.load_item_data(self.editing_item, editable=True)
        else:
            # Save the edited data
            if self.save_edited_data():
                self.editing_enabled = False
                self.edit_button.config(text='Edit Row')

    def load_item_data(self, item, editable=False):
        values = self.table_view.item(item, 'values')
        for i, col in enumerate(self.table_view['columns']):
            if editable:
                self.table_view.set(item, col, values[i])
                self.table_view.item(item, tags=(col,))
            else:
                self.table_view.item(item, tags=())

    def save_edited_data(self):
        if self.editing_enabled and self.editing_item:
            values = self.table_view.item(self.editing_item, 'values')
            new_values = []
            for i, col in enumerate(self.table_view['columns']):
                new_value = self.table_view.set(self.editing_item, col)
                new_values.append(new_value)
            self.table_view.item(self.editing_item, values=new_values)
            return True
        return False

    def update_table_list(self):
        self.table_list['values'] = self.get_table_names()


    def delete_selected_table(self):
        selected_table = self.table_list.get()
        if selected_table:
            confirmation = messagebox.askyesno(
                'Confirm Deletion',
                f'Are you sure you want to delete the table "{selected_table}"? This action cannot be undone.'
            )
            if confirmation:
                connection = sqlite3.connect(self.database_filename)
                cursor = connection.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {selected_table}")
                connection.commit()
                connection.close()
                self.update_table_list()
                self.table_list.set('')  # Clear the table selection
                messagebox.showinfo('Table Deleted', f'Table "{selected_table}" has been deleted.')

    def get_table_names(self):
        connection = sqlite3.connect(self.database_filename)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        connection.close()
        return [table[0] for table in tables]

    def on_table_select(self, event):
        selected_table = self.table_list.get()
        if selected_table:
            connection = sqlite3.connect(self.database_filename)
            cursor = connection.cursor()
            cursor.execute(f"PRAGMA table_info({selected_table});")  # Get column names and details
            columns_info = cursor.fetchall()
            cursor.execute(f"SELECT * FROM {selected_table}")
            rows = cursor.fetchall()
            connection.close()
    
            # Clear existing data and columns
            for i in self.table_view.get_children():
                self.table_view.delete(i)
            for col in self.table_view['columns']:
                self.table_view.column(col, width=0)  # Hide the columns
    
            # Add a temporary index column
            self.table_view.heading('#0', text='Index')
            self.table_view.column('#0', width=7, minwidth=10, anchor='center')  # Adjust the width as needed and set anchor to 'center'
            
            # Add column names to Treeview
            self.table_view['columns'] = ['index'] + [col_info[1] for col_info in columns_info]
            
            # Set the column identifier and anchor for other columns
            for col_info in columns_info:
                col_name = col_info[1]
                self.table_view.heading(col_name, text=col_name)
                self.table_view.column(col_name, width=10, anchor='w')  # Adjust the width as needed and set anchor to 'w' (west)
    
            # Add new data with a temporary index
            for i, row in enumerate(rows, start=1):
                self.table_view.insert('', 'end', values=(i,) + row)
    
    
    
    
    def highlight_rows_by_range(self, range_text):
        selected_table = self.table_list.get()

        if selected_table and range_text:
            try:
                selected_indices = []
    
                # Handle the case where indices are specified as a range (e.g., "3-7")
                for part in range_text.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_indices.extend(range(start, end + 1))
                    else:
                        selected_indices.append(int(part))
    
                if selected_indices:
                    # Clear previous selections
                    for item in self.table_view.selection():
                        self.table_view.selection_remove(item)
    
                    # Select the rows in the table based on indices
                    for index in selected_indices:
                        item = self.table_view.get_children()[index - 1]  # -1 to adjust for 0-based indexing
                        self.table_view.selection_add(item)
                        # Scroll the table to make the selected row visible
                        self.table_view.see(item)
            except ValueError: pass


    def remove_selected_rows(self):
        selected_table = self.table_list.get()
        selected_indices_text = self.row_range_entry.get()  # Use self.row_range_entry instead of self.index_entry
        
        if selected_table and selected_indices_text:
            try:
                selected_indices = []
    
                # Handle the case where indices are specified as a range (e.g., "3-7")
                for part in selected_indices_text.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected_indices.extend(range(start, end + 1))
                    else:
                        selected_indices.append(int(part))
    
                if selected_indices:
                    confirmation_message = self.get_confirmation_message(selected_indices)
    
                    confirmation = messagebox.askyesno(
                        'Confirm Deletion',
                        confirmation_message
                    )
    
                    if confirmation:
                        connection = sqlite3.connect(self.database_filename)
                        cursor = connection.cursor()
                        for index in selected_indices:
                            cursor.execute(f"DELETE FROM {selected_table} WHERE rowid=?", (index,))
                        connection.commit()
                        connection.close()
                        self.update_table_list()
                        self.on_table_select(None)  # Refresh the table view
                        messagebox.showinfo('Rows Deleted', f'Selected rows have been deleted.')
            except ValueError:
                pass
                #messagebox.showerror('Invalid Range', 'Please enter a valid range (e.g., "3-7").')
    
    def get_confirmation_message(self, selected_indices):
        if len(selected_indices) <= 25:
            return f'Are you sure you want to delete rows {", ".join(map(str, selected_indices))}?'
        else:
            return f'Are you sure you want to delete rows {selected_indices[0]}-{selected_indices[-1]}?'
    
    def on_index_entry_change(self, event):
        range_text = self.index_entry.get()
        self.highlight_rows_by_range(range_text)


class DatabaseSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Select Database')
        self.geometry("300x100")  # Set the initial window size
        
        # Create a label to instruct the user
        label = tk.Label(self, text="Please select a database file:")
        label.pack(pady=10)
        
        # Create a button to open a file dialog
        select_button = ttk.Button(self, text="Select Database", command=self.select_database)
        select_button.pack()
        
        # Initialize the database filename
        self.database_filename = None

    def select_database(self):
        # Open a file dialog to select a database file
        file_path = filedialog.askopenfilename(filetypes=[("Database files", "*.db")])

        if file_path:
            self.database_filename = file_path
            self.destroy()  # Close the database selection window
            self.open_main_application()

    def open_main_application(self):
        # After selecting a database, open the main application window
        app = SQLiteViewer(self.database_filename)
        app.mainloop()
    
if __name__ == '__main__':
    db_selector = DatabaseSelector()
    db_selector.mainloop()
