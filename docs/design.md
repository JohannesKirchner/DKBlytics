### Database
- Table: Transactions (Text, Entity, Account, Amount, Date)
- Table: Accounts (Name, Balance)
- Table: Categories (Text, Entity, Category)

### API
- Get DKB update
    - Get DKB info of current balance
    - Get DKB update of recent transactions (after last update)
    - Post all transactions by id
    - Update current balance
- Get transaction by id
- Post transaction by id
- Update transaction type by id
- Get all transactions filtered by Type and min and max Date
- Get balance by id
- Post balance by id
- Update balance by id
- Get all balances

### UI
#### View 1 - Categorization
- Update Button —> get recent transactions and balance from DKB and update database
- Create new categories and optionally link them to already existing categories to parent-child relationships
- Assign or re-assign transaction to categories per Drag-and-Drop following the category rules schme the api provides
#### View 2 - Transactions
- Transactions as bar chart by type for given month or year (Right Sidebar is a list with recent transactions grouped by type)
#### View 3 - Balancd
- Balance development as line chart agains days, months or years (chooseable balance type)
