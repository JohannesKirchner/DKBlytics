<div class="mt-16 mx-10 flex flex-row gap-[5%] items-center">
    <div class="w-[60%] h-[80vh] flex flex-col">
        <div class="flex flex-row justify-center items-center gap-3">
            <h1 class="text-3xl">Averaged Expense Breakdown</h1>
            <span class="text-3xl font-extrabold">2025</span>
        </div>
    
        <div class="flex-1 flex justify-center items-center border-2 rounded-lg">
            <span class="text-xl">Sankey Chart</span>
        </div>
    </div>

    <div class="w-[35%] h-[50vh] flex flex-col">
        <div class="flex justify-center">
            <h1 class="text-2xl">Expenses for Category over time</h1>
        </div>

        <div class="flex-1 flex justify-center items-center border-2 rounded-lg">
            <span class="text-xl">Line Chart</span>
        </div>

    </div>
</div>

<p>
    Hovering or clicking on certain sankey elements should display the expenses over time
    of this particular category in the panel to the right.

    There should also be a filter panel for defining the time range for which to display
    the Sankey. I think for the Sankey, only per year really makes sense. But to make it
    more accessible it should show the average values per month for a given year. So the
    filter panel only needs the year.

    Maybe additional Pie Chart mapping Income to 2nd level Expenses would be a nice 
    addition on the right hand side
</p>