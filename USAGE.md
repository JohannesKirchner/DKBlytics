# DKBlytics User Guide 📖

This comprehensive guide walks you through all features of DKBlytics, from initial setup to advanced financial analytics. Whether you're just getting started or looking to master specific features, this guide has you covered.

## 🚀 **Getting Started**

### **First Time Setup**

1. **Launch DKBlytics**
   ```bash
   # Start backend (Terminal 1)
   cd backend && python -m src.main
   
   # Start frontend (Terminal 2)  
   cd frontend-nicegui && python -m app.main
   ```

2. **Access the Application**
   - Open your browser to `http://localhost:8081`
   - You'll see the Dashboard with quick action buttons

3. **Initial Data Setup**
   - Start by creating expense and income categories
   - Import your transaction data (CSV or manual entry)
   - Set up categorization rules for automatic classification

---

## 🏠 **Dashboard Overview**

The Dashboard serves as your financial command center, providing:

### **Quick Actions**
- **Categorize Transactions** - Jump to transaction management
- **Manage Categories** - Set up your financial categories  
- **View Balance** - See balance evolution and analytics
- **Budget Overview** - Monitor budgets and spending goals

### **Getting Started Guide**
The dashboard includes a helpful checklist:
1. Create your expense/income categories
2. Assign uncategorized transactions to categories
3. Review your spending patterns and balance
4. Monitor your monthly/yearly budget

---

## 💳 **Transaction Management**

The Transactions page is where you'll spend most of your time managing and categorizing your financial data.

### **Viewing Transactions**

#### **Transaction Table**
The main table displays all transactions with columns:
- **Date** - Transaction booking date
- **Account** - Source account name  
- **Entity** - Counterparty (store, person, institution)
- **Description** - Transaction text/memo
- **Amount** - Transaction value (+ for income, - for expenses)
- **Category** - Assigned category (or "Uncategorized")
- **Reference** - Additional reference information

#### **Advanced Filtering**

**Filter Controls:**
```
┌─────────────────────────────────────────────────────────┐
│ Filters                                                 │
│ ┌─────────┬──────────┬──────────┬──────────┬─────────┐   │
│ │From Date│ To Date  │ Account  │ Category │ Sort By │   │
│ │         │          │          │          │         │   │
│ │ Search  │ Per Page │ [Apply]  │ [Clear]  │         │   │
│ └─────────┴──────────┴──────────┴──────────┴─────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Filter Options:**
- **Date Range** - Select specific time periods
- **Account Filter** - View specific accounts or all accounts
- **Category Filter** - Show specific categories or uncategorized transactions
- **Sort Options** - Date (newest/oldest), Amount (high to low/low to high)
- **Text Search** - Search in entity, description, and reference fields
- **Page Size** - 25, 50, 100, or 200 transactions per page

**Quick Date Selection:**
- **30d** - Last 30 days
- **90d** - Last 90 days  
- **1y** - Last year

#### **Pagination**
Navigate large datasets with:
- Previous/Next buttons
- Page information display ("Page 2 of 15 (743 total)")
- Jump to specific page functionality

### **Categorizing Transactions**

#### **Manual Categorization**

1. **Select Transactions**
   - Use checkboxes to select one or multiple transactions
   - Selected transactions are highlighted

2. **Choose Category**
   - Select target category from dropdown
   - Categories are organized hierarchically

3. **Create Rules**
   - **Exact Rules** - Match entity + description exactly
   - **Entity Rules** - Match entity only (applies to all transactions from this entity)

#### **Rule Types Explained**

**Exact Rules:**
```
Transaction: "AMAZON.DE" + "Order 123-456"
Rule Created: Entity="AMAZON.DE" AND Text="Order 123-456" → Category="Online Shopping"
Result: Only this specific transaction type will be categorized automatically
```

**Entity Rules:**
```
Transaction: "AMAZON.DE" + "Order 123-456"  
Rule Created: Entity="AMAZON.DE" AND Text=null → Category="Online Shopping"
Result: ALL transactions from AMAZON.DE will be categorized as "Online Shopping"
```

#### **Automatic Rule Application**

Use the **"Apply All Rules"** button to:
- Re-categorize all transactions based on current rules
- Apply newly created rules to historical transactions
- Resolve rule conflicts (exact rules override entity rules)
- Get detailed statistics on categorization results

### **Best Practices**

#### **Categorization Strategy**
1. **Start with Entity Rules** - Create broad categories for common merchants
2. **Add Exact Rules** - Handle special cases or specific transaction types
3. **Regular Maintenance** - Review and adjust rules as spending patterns change

#### **Efficient Workflow**
1. **Filter for Uncategorized** - Set category filter to "null"
2. **Group Similar Transactions** - Sort by entity to group similar transactions
3. **Batch Categorization** - Select multiple similar transactions at once
4. **Apply Rules Regularly** - Use "Apply All Rules" after creating new rules

---

## 🏷️ **Category Management**

Categories organize your transactions into meaningful groups for analysis and budgeting.

### **Category Hierarchy**

#### **Hierarchical Structure**
```
📊 Expenses
├── 🛒 Shopping
│   ├── Groceries
│   ├── Clothing
│   └── Online Shopping
├── 🚗 Transportation
│   ├── Fuel
│   ├── Public Transport
│   └── Parking
└── 🏠 Housing
    ├── Rent
    ├── Utilities
    └── Maintenance

💰 Income
├── Salary
├── Freelancing
└── Investments
```

### **Managing Categories**

#### **Creating Categories**

1. **Add New Category**
   ```
   ┌─────────────────────────────────────┐
   │ Add New Category                    │
   │ ┌─────────────┬─────────────────────┐ │
   │ │ Name        │ Parent Category     │ │
   │ │ [Groceries] │ [Shopping        ▼] │ │
   │ │             │                     │ │
   │ │          [Add Category]           │ │
   │ └─────────────┴─────────────────────┘ │
   └─────────────────────────────────────┘
   ```

2. **Category Properties**
   - **Name** - Descriptive category name
   - **Parent** - Optional parent category for hierarchy
   - **Leave blank** for root-level categories

#### **Category Table**
View all categories with:
- **Name** - Category name with hierarchy indicated
- **Parent** - Direct parent category
- **Actions** - Delete button for unused categories

#### **Deleting Categories**
- Only categories without assigned transactions can be deleted
- System prevents accidental deletion of categories in use
- Consider reassigning transactions before deleting categories

### **Category Best Practices**

#### **Hierarchical Organization**
```
✅ Good Hierarchy:
Expenses → Shopping → Groceries
Expenses → Transportation → Fuel

❌ Flat Structure:
Groceries
Fuel  
Rent
Salary
```

#### **Naming Conventions**
- **Be Specific** - "Groceries" vs "Food"
- **Use Consistent Terms** - "Fuel" not "Gas/Petrol/Gasoline"
- **Avoid Abbreviations** - "Transportation" not "Transport/Trans"

#### **Common Category Structures**

**Personal Finance:**
```
Income
├── Salary
├── Bonuses
└── Side Income

Expenses
├── Fixed Costs
│   ├── Rent/Mortgage
│   ├── Insurance
│   └── Utilities
├── Variable Costs
│   ├── Groceries
│   ├── Entertainment
│   └── Transportation
└── Savings & Investments
    ├── Emergency Fund
    └── Retirement
```

---

## 📊 **Balance Analytics**

The Balance page provides comprehensive insights into your financial health and spending patterns.

### **Balance Overview**

#### **Summary Cards**
The dashboard displays four key metrics:

**Current Balance Card**
```
┌─────────────────────┐
│ Current Balance     │
│ €2,847.93          │
│ of €3,200.00 total  │
└─────────────────────┘
```

**Period Income Card**
```
┌─────────────────────┐
│ Period Income       │
│ €4,200.00          │
│ From 12 transactions│
└─────────────────────┘
```

**Period Expenses Card**
```
┌─────────────────────┐
│ Period Expenses     │
│ €3,847.50          │
│ From 89 transactions│
└─────────────────────┘
```

**Net Change Card**
```
┌─────────────────────┐
│ Net Change          │
│ +€352.50           │
│ This period         │
└─────────────────────┘
```

### **Interactive Charts**

#### **Balance Evolution Chart**
- **Line chart** showing balance changes over time
- **Historical accuracy** - Uses real account balances, not running totals
- **Hover details** - Exact balance and date for each point
- **Time period filtering** - Adjust date range to focus on specific periods

#### **Income vs Expenses Chart**
- **Column chart** comparing monthly income and expenses
- **Color coded** - Green for income, red for expenses
- **Monthly breakdown** - Easy to spot spending patterns and trends
- **Trend analysis** - Identify seasonal patterns or unusual months

#### **Multi-Account Balance Chart** *(When viewing all accounts)*
- **Multiple line chart** with different colors for each account
- **Comparative analysis** - See which accounts are growing or declining
- **Account legend** - Toggle individual accounts on/off
- **Balance trends** - Understand how each account contributes to total wealth

### **Filtering Options**

#### **Account Selection**
- **All Accounts** - Combined view of all accounts
- **Specific Account** - Focus on individual account performance
- **Account comparison** - Multi-account charts available when viewing all

#### **Date Range Controls**
```
┌─────────────────────────────────────────────────┐
│ Filters                                         │
│ ┌─────────┬─────────┬─────────┬─────────────────┐ │
│ │ Account │From Date│ To Date │ Quick Select    │ │
│ │ [All ▼] │[Date]   │[Date]   │[30d][90d][1y]  │ │
│ │         │         │         │      [Update]   │ │
│ └─────────┴─────────┴─────────┴─────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Quick Date Options:**
- **30d** - Last 30 days (good for recent trends)
- **90d** - Last 90 days (quarterly view)
- **1y** - Last year (annual overview)
- **Custom** - Any date range using date pickers

### **Understanding Your Balance Data**

#### **Balance Calculation**
DKBlytics uses **historical accuracy**:
1. Starts with current account balance
2. Works backwards through transaction history
3. Shows actual balance at each point in time
4. Accounts for all transactions in the selected period

#### **Data Limitations**
- **500 Transaction Limit** - Charts show up to 500 most recent transactions
- **For high-volume accounts**, consider shorter date ranges for complete accuracy
- **Future Enhancement** - Pagination will eliminate this limitation

#### **Interpretation Tips**

**Balance Evolution:**
- **Upward trend** - Growing wealth/savings
- **Downward trend** - Spending more than earning
- **Steep drops** - Large expenses or unusual spending
- **Steady growth** - Consistent saving patterns

**Income vs Expenses:**
- **Green > Red** - Profitable months (income exceeds expenses)  
- **Red > Green** - Deficit months (expenses exceed income)
- **Consistent patterns** - Regular income/expense cycles
- **Seasonal variations** - Holiday spending, annual bonuses, etc.

---

## 🎯 **Budget Tracking** *(Coming Soon)*

Budget functionality is planned for future releases and will include:

### **Planned Features**
- **Monthly Budget Planning** - Set spending limits by category
- **Budget vs Actual Analysis** - Compare planned vs actual spending
- **Budget Alerts** - Notifications when approaching limits
- **Savings Goals** - Track progress toward financial objectives
- **Yearly Budget Overview** - Annual planning and review

### **Current Workarounds**
While dedicated budgeting features are in development, you can:
1. **Use Balance Analytics** - Monitor spending trends
2. **Category Analysis** - Review spending by category in transaction filters
3. **Manual Tracking** - Export data for external budget tools

---

## 🔄 **Data Import & Export**

### **Transaction Import**

#### **Manual Transaction Entry**
Currently, transactions are primarily imported through the API or entered via the backend. A user-friendly import interface is planned for future releases.

#### **DKB Integration** 
DKBlytics includes DKB banking integration capabilities:
- **CSV Import** - Process DKB transaction exports
- **Automated Data Extraction** - Parse transaction details
- **Duplicate Detection** - Prevent duplicate transaction entries

### **Planned Import Features**
- **Web-based CSV Upload** - Drag-and-drop import interface
- **Multiple Bank Support** - Support for other German banks
- **File Format Validation** - Automatic format detection and validation

---

## ⚙️ **Advanced Features**

### **Category Rules Engine**

#### **Rule Priority System**
Rules are applied in priority order:
1. **Exact Rules** (Entity + Text match) - Highest priority
2. **Entity Rules** (Entity only) - Default fallback

#### **Bulk Rule Application**
The "Apply All Rules" feature:
- **Recategorizes** all existing transactions
- **Handles conflicts** using priority system
- **Provides statistics** on categorization results
- **Updates historical data** retroactively

#### **Rule Management Best Practices**

**Start Broad, Get Specific:**
```
1. Create Entity Rules for common merchants:
   REWE → Groceries
   Shell → Fuel
   
2. Add Exact Rules for special cases:
   Shell + "Car Wash" → Car Maintenance
   REWE + "Alcohol" → Entertainment
```

**Regular Maintenance:**
- Review uncategorized transactions monthly
- Update rules as spending patterns change
- Clean up unused or overly specific rules

### **Data Accuracy & Validation**

#### **Transaction Deduplication**
- **Fingerprint System** - Unique hash for each transaction
- **Batch Processing** - Handle multiple imports safely
- **Conflict Resolution** - Prevent accidental duplicates

#### **Balance Accuracy**
- **Real Account Balances** - Uses actual current balances as baseline
- **Historical Calculation** - Works backwards through transaction history
- **Data Validation** - Ensures mathematical accuracy

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Charts Not Loading**
**Symptoms:** Blank chart areas or "Chart loading..." messages
**Solutions:**
1. Ensure `nicegui[highcharts]` is installed: `uv add "nicegui[highcharts]"`
2. Check browser console for JavaScript errors
3. Verify backend API is running and accessible

#### **Connection Warnings**
**Symptoms:** "Connection lost. Trying to reconnect" messages
**Explanation:** Normal during development when server restarts
**Solutions:** 
- Messages disappear when connection restores
- If persistent, check server logs for errors

#### **Transaction Limit Warnings**
**Symptoms:** Charts show incomplete data or "Limited to 500 transactions" messages
**Solutions:**
1. Use shorter date ranges for high-volume accounts
2. Focus on specific accounts rather than "All Accounts"
3. Future releases will implement pagination

#### **Slow Performance**
**Symptoms:** Pages load slowly or timeout
**Solutions:**
1. Reduce date range for large datasets
2. Filter by specific accounts or categories
3. Check backend server performance

#### **Category Rule Conflicts**
**Symptoms:** Transactions categorized unexpectedly
**Solutions:**
1. Review rule priority (exact rules override entity rules)
2. Use "Apply All Rules" to recalculate all categorizations
3. Check for conflicting entity and exact rules

### **Data Issues**

#### **Missing Transactions**
1. Check date range filters
2. Verify account selection includes the relevant accounts
3. Ensure transactions were imported correctly

#### **Incorrect Categorization**
1. Review category rules for the affected entity
2. Check for exact vs entity rule conflicts
3. Manually recategorize and create more specific rules

#### **Balance Discrepancies**
1. Verify account balance is current in the database
2. Check for missing or duplicate transactions
3. Ensure all relevant transactions are in the date range

---

## 💡 **Tips & Best Practices**

### **Effective Financial Management**

#### **Regular Maintenance Schedule**
- **Weekly** - Review and categorize new transactions
- **Monthly** - Analyze spending patterns and trends
- **Quarterly** - Review and update category rules
- **Yearly** - Comprehensive financial review and goal setting

#### **Category Strategy**
- **Keep It Simple** - Don't over-categorize initially
- **Be Consistent** - Use the same categories for similar transactions
- **Review Regularly** - Adjust categories as life changes
- **Use Hierarchy** - Organize related categories under parent categories

#### **Rule Management**
- **Start General** - Create entity rules for common merchants
- **Add Specificity** - Use exact rules for special cases only
- **Regular Cleanup** - Remove unused or overly specific rules
- **Test Changes** - Use "Apply All Rules" after rule modifications

### **Data Analysis Strategies**

#### **Spending Pattern Analysis**
1. **Use date filters** to compare different time periods
2. **Sort by amount** to identify largest expenses
3. **Filter by category** to understand specific spending areas
4. **Review balance evolution** for overall financial health

#### **Financial Health Monitoring**
- **Track net change** - Ensure consistent positive cash flow
- **Monitor account balances** - Avoid overdrafts and maintain buffers
- **Analyze spending trends** - Identify areas for potential savings
- **Set category budgets** - Use transaction data to inform budget decisions

### **Performance Optimization**

#### **Working with Large Datasets**
- **Use date range filters** to limit data processing
- **Filter by account** when analyzing specific accounts
- **Use pagination** to navigate large transaction sets efficiently
- **Consider data archiving** for very old transactions

---

## 🔮 **Future Enhancements**

### **Planned Features**

#### **Short Term** (Next Release)
- **Enhanced Budget Tracking** - Comprehensive budgeting tools
- **Data Export** - CSV and PDF export functionality
- **Mobile Responsive Design** - Better mobile device support
- **Advanced Filtering** - More sophisticated search options

#### **Medium Term** 
- **Multi-Bank Support** - Support for additional German banks
- **Automated Transaction Fetching** - Direct bank API integration
- **Financial Goal Tracking** - Savings and investment goal monitoring
- **Advanced Analytics** - Predictive spending models and insights

#### **Long Term**
- **Mobile App** - Native mobile application
- **Multi-Currency Support** - Handle multiple currencies
- **Investment Tracking** - Portfolio and investment analysis
- **Tax Preparation** - Export data for tax purposes

### **User-Requested Features**

We're constantly improving DKBlytics based on user feedback. Common requests include:
- **Better search functionality** - More powerful transaction search
- **Custom date ranges** - Fiscal year and custom period support
- **Report generation** - Automated monthly/yearly reports
- **Data backup** - Export/import complete database

---

## 📞 **Getting Help**

### **Documentation Resources**
- **README.md** - Project overview and setup instructions
- **CONTRIBUTION.md** - Development guidelines and technical details
- **This Guide (USAGE.md)** - Comprehensive feature documentation
- **CHANGELOG.md** - Version history and recent updates

### **Technical Support**

#### **Self-Help Resources**
1. **Check this guide** for feature-specific help
2. **Review troubleshooting section** for common issues
3. **Check browser console** for JavaScript errors
4. **Verify API documentation** at `http://localhost:8000/docs`

#### **Reporting Issues**
When reporting problems, please include:
- **Step-by-step reproduction** - What you were doing when the issue occurred
- **Error messages** - Full text of any error messages
- **Browser information** - Browser type and version
- **Data context** - Approximate number of transactions, date ranges, etc.

### **Feature Requests**

We welcome suggestions for new features! When requesting features:
- **Describe the use case** - What problem would this solve?
- **Provide examples** - How would you use this feature?
- **Consider alternatives** - Are there existing features that might work?
- **Think about integration** - How should it work with existing features?

---

**Happy Financial Management! 📊💰**

Remember, DKBlytics is designed to grow with your financial management needs. Start simple with basic categorization and gradually explore advanced features as you become more comfortable with the system.